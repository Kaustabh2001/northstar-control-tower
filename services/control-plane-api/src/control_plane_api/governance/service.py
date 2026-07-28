from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from northstar_contracts import GovernanceState

from ..auth import CurrentUser
from ..models import (
    AssetRecord,
    AuditEventRecord,
    GovernanceApprovalRecord,
    GovernanceEvidenceRecord,
    AssetDetailRecord,
)
from ..schemas import AssetResponse, GovernanceApproval, GovernanceEvidence, GovernancePortfolio
from ..registry.service import to_response
from .policy import ALLOWED_TRANSITIONS, REQUIRED_EVIDENCE


def _approval_view(
    approval: GovernanceApprovalRecord,
    asset: AssetRecord,
) -> GovernanceApproval:
    return GovernanceApproval(
        **{
            column: getattr(approval, column)
            for column in (
                "approval_id",
                "asset_id",
                "version",
                "target_state",
                "status",
                "requested_by",
                "request_note",
                "decided_by",
                "decision_note",
                "created_at",
                "decided_at",
            )
        },
        display_name=asset.display_name,
        asset_type=asset.asset_type,
        current_state=asset.governance_state,
    )


def governance_portfolio(session: Session) -> GovernancePortfolio:
    approvals = session.scalars(
        select(GovernanceApprovalRecord).order_by(
            GovernanceApprovalRecord.created_at.desc()
        )
    ).all()
    approval_views = []
    for approval in approvals:
        asset = session.get(AssetRecord, (approval.asset_id, approval.version))
        if asset:
            approval_views.append(_approval_view(approval, asset))
    evidence = session.scalars(
        select(GovernanceEvidenceRecord).order_by(
            GovernanceEvidenceRecord.created_at.desc()
        )
    ).all()
    state_counts = dict(
        session.execute(
            select(AssetRecord.governance_state, func.count()).group_by(
                AssetRecord.governance_state
            )
        ).all()
    )
    return GovernancePortfolio(
        approvals=approval_views,
        evidence=[GovernanceEvidence.model_validate(item) for item in evidence],
        state_counts=state_counts,
        allowed_transitions=ALLOWED_TRANSITIONS,
    )


def request_asset_approval(
    session: Session,
    *,
    asset_id: str,
    version: str,
    target_state: GovernanceState,
    note: str,
    actor: CurrentUser,
) -> GovernanceApproval:
    asset = session.get(AssetRecord, (asset_id, version))
    if not asset:
        raise LookupError("Asset version not found.")
    if target_state.value not in ALLOWED_TRANSITIONS.get(asset.governance_state, []):
        raise ValueError(
            f"Transition {asset.governance_state} -> {target_state.value} is not allowed."
        )
    evidence_types = set(
        session.scalars(
            select(GovernanceEvidenceRecord.evidence_type)
            .where(GovernanceEvidenceRecord.asset_id == asset_id)
            .where(GovernanceEvidenceRecord.version == version)
            .where(GovernanceEvidenceRecord.status == "accepted")
        )
    )
    missing = REQUIRED_EVIDENCE.get(target_state.value, set()) - evidence_types
    if missing:
        raise ValueError(f"Missing required evidence: {', '.join(sorted(missing))}.")
    if target_state == GovernanceState.PRODUCTION:
        detail = session.get(AssetDetailRecord, (asset_id, version))
        dependencies = (detail.payload if detail else {}).get("dependencies", [])
        blocked = []
        for dependency in dependencies:
            if not isinstance(dependency, str) or ":" not in dependency:
                continue
            dependency_id, dependency_version = dependency.rsplit(":", 1)
            dependency_asset = session.get(
                AssetRecord,
                (dependency_id, dependency_version),
            )
            if (
                not dependency_asset
                or dependency_asset.governance_state
                not in {"shadow", "canary", "production"}
            ):
                blocked.append(dependency)
        if blocked:
            raise ValueError(
                "Dependencies are not runtime-approved: "
                + ", ".join(sorted(blocked))
                + "."
            )
    approval = GovernanceApprovalRecord(
        approval_id=str(uuid4()),
        asset_id=asset_id,
        version=version,
        target_state=target_state.value,
        status="pending",
        requested_by=actor.email,
        request_note=note,
    )
    session.add(approval)
    session.add(
        AuditEventRecord(
            event_id=str(uuid4()),
            asset_id=asset_id,
            version=version,
            action="governance.approval.requested",
            actor_subject=actor.subject,
            actor_email=actor.email,
            detail=f"Requested {asset.governance_state} -> {target_state.value}: {note}",
        )
    )
    session.commit()
    session.refresh(approval)
    return _approval_view(approval, asset)


def decide_asset_approval(
    session: Session,
    *,
    approval_id: str,
    decision: str,
    note: str,
    actor: CurrentUser,
) -> GovernanceApproval | None:
    approval = session.get(GovernanceApprovalRecord, approval_id)
    if not approval or approval.status != "pending":
        return None
    if approval.requested_by == actor.email:
        raise ValueError("The requester cannot approve their own lifecycle request.")
    asset = session.get(AssetRecord, (approval.asset_id, approval.version))
    if not asset:
        return None
    approval.status = "approved" if decision == "approve" else "rejected"
    approval.decided_by = actor.email
    approval.decision_note = note
    approval.decided_at = datetime.now(UTC)
    if decision == "approve":
        asset.governance_state = approval.target_state
        asset.updated_at = datetime.now(UTC)
    session.add(
        AuditEventRecord(
            event_id=str(uuid4()),
            asset_id=asset.asset_id,
            version=asset.version,
            action=f"governance.approval.{approval.status}",
            actor_subject=actor.subject,
            actor_email=actor.email,
            detail=f"{approval.target_state}: {note}",
        )
    )
    session.commit()
    session.refresh(approval)
    return _approval_view(approval, asset)


def emergency_lifecycle_action(
    session: Session,
    *,
    asset_id: str,
    version: str,
    action: str,
    reason: str,
    target_version: str | None,
    actor: CurrentUser,
) -> AssetResponse:
    asset = session.get(AssetRecord, (asset_id, version))
    if not asset:
        raise LookupError("Asset version not found.")
    if action == "suspend":
        if asset.governance_state in {"retired", "suspended"}:
            raise ValueError("Only active assets can be suspended.")
        asset.governance_state = "suspended"
        detail = f"Emergency suspension: {reason}"
    else:
        if not target_version:
            raise ValueError("Rollback requires target_version.")
        target = session.get(AssetRecord, (asset_id, target_version))
        if not target:
            raise LookupError("Rollback target version not found.")
        if target.governance_state in {"retired", "suspended"}:
            raise ValueError("Rollback target is not deployable.")
        asset.governance_state = "suspended"
        target.governance_state = "production"
        target.updated_at = datetime.now(UTC)
        detail = f"Rolled back to {target_version}: {reason}"
    asset.updated_at = datetime.now(UTC)
    session.add(
        AuditEventRecord(
            event_id=str(uuid4()),
            asset_id=asset_id,
            version=version,
            action=f"governance.emergency.{action}",
            actor_subject=actor.subject,
            actor_email=actor.email,
            detail=detail,
        )
    )
    session.commit()
    session.refresh(asset)
    return to_response(asset)
