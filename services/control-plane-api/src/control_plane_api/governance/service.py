from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from northstar_contracts import GovernanceState

from ..auth import CurrentUser
from ..models import AssetRecord, GovernanceApprovalRecord, GovernanceEvidenceRecord
from ..schemas import GovernanceApproval, GovernanceEvidence, GovernancePortfolio
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
    session.commit()
    session.refresh(approval)
    return _approval_view(approval, asset)
