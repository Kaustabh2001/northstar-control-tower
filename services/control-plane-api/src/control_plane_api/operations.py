from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from northstar_contracts import GovernanceState

from .auth import CurrentUser
from .models import (
    AssetRecord,
    GovernanceApprovalRecord,
    GovernanceEvidenceRecord,
    HumanReviewRecord,
    McpInvocationRecord,
    RuntimeEventRecord,
    WorkflowRunRecord,
)
from .schemas import (
    GovernanceApproval,
    GovernanceEvidence,
    GovernancePortfolio,
    HumanReviewView,
    McpInvocationView,
    RuntimeEventView,
    RuntimePortfolio,
    RuntimeStage,
    RunDetailResponse,
    WorkflowRunView,
)


ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "discovered": ["registered", "retired"],
    "registered": ["assess", "retired"],
    "assess": ["build_test", "retired"],
    "build_test": ["steward_review", "retired"],
    "steward_review": ["shadow", "build_test", "retired"],
    "shadow": ["canary", "suspended", "retired"],
    "canary": ["production", "suspended", "retired"],
    "production": ["suspended", "retired"],
    "suspended": ["assess", "retired"],
    "retired": [],
}

REQUIRED_EVIDENCE: dict[str, set[str]] = {
    "build_test": {"risk_assessment"},
    "steward_review": {"test_report"},
    "shadow": {"risk_assessment", "test_report"},
    "canary": {"monitoring_plan"},
    "production": {"monitoring_plan", "rollback_plan"},
}


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
        evidence=[
            GovernanceEvidence.model_validate(item) for item in evidence
        ],
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


def _run_view(run: WorkflowRunRecord) -> WorkflowRunView:
    return WorkflowRunView(
        **{
            column: getattr(run, column)
            for column in (
                "run_id",
                "workflow_asset_id",
                "workflow_version",
                "status",
                "current_stage_id",
                "correlation",
                "checkpoint_ref",
                "error_code",
                "error_summary",
                "started_at",
                "updated_at",
            )
        },
        workflow_name="Employee Access Request",
        stages=[RuntimeStage.model_validate(stage) for stage in run.stages],
    )


def runtime_portfolio(session: Session) -> RuntimePortfolio:
    runs = session.scalars(
        select(WorkflowRunRecord).order_by(WorkflowRunRecord.updated_at.desc())
    ).all()
    reviews = session.scalars(
        select(HumanReviewRecord).order_by(HumanReviewRecord.requested_at.desc())
    ).all()
    status_counts = dict(
        session.execute(
            select(WorkflowRunRecord.status, func.count()).group_by(
                WorkflowRunRecord.status
            )
        ).all()
    )
    return RuntimePortfolio(
        runs=[_run_view(run) for run in runs],
        reviews=[HumanReviewView.model_validate(review) for review in reviews],
        status_counts=status_counts,
    )


def run_detail(session: Session, run_id: str) -> RunDetailResponse | None:
    run = session.get(WorkflowRunRecord, run_id)
    if not run:
        return None
    events = session.scalars(
        select(RuntimeEventRecord)
        .where(RuntimeEventRecord.run_id == run_id)
        .order_by(RuntimeEventRecord.occurred_at)
    ).all()
    review = session.scalar(
        select(HumanReviewRecord)
        .where(HumanReviewRecord.run_id == run_id)
        .order_by(HumanReviewRecord.requested_at.desc())
    )
    return RunDetailResponse(
        run=_run_view(run),
        events=[RuntimeEventView.model_validate(event) for event in events],
        review=HumanReviewView.model_validate(review) if review else None,
    )


def decide_human_review(
    session: Session,
    *,
    review_id: str,
    decision: str,
    rationale: str,
    actor: CurrentUser,
) -> RunDetailResponse | None:
    review = session.get(HumanReviewRecord, review_id)
    if not review or review.status != "pending":
        return None
    run = session.get(WorkflowRunRecord, review.run_id)
    if not run:
        return None
    now = datetime.now(UTC)
    review.status = "approved" if decision == "approve" else "rejected"
    review.decision = decision
    review.decided_by = actor.email
    review.rationale = rationale
    review.decided_at = now
    stages = list(run.stages)
    for stage in stages:
        if stage["stage_id"] == review.stage_id:
            stage["status"] = "completed" if decision == "approve" else "failed"
            stage["completed_at"] = now.isoformat()
            stage["summary"] = rationale
    run.stages = stages
    run.status = "running" if decision == "approve" else "failed"
    run.current_stage_id = "provision-access" if decision == "approve" else review.stage_id
    run.error_code = None if decision == "approve" else "HUMAN_REJECTED"
    run.error_summary = None if decision == "approve" else rationale
    run.updated_at = now
    session.add(
        RuntimeEventRecord(
            event_id=str(uuid4()),
            run_id=run.run_id,
            event_type="human.decision.recorded",
            stage_id=review.stage_id,
            actor_id=actor.email,
            payload={"decision": decision, "rationale": rationale},
        )
    )
    session.commit()
    return run_detail(session, run.run_id)


TOOL_POLICY = {
    "lookup_access_policy": {
        "roles": {"viewer", "operator", "reviewer", "admin"},
        "stage": None,
    },
    "validate_entitlement": {
        "roles": {"operator", "reviewer", "admin"},
        "stage": "policy-evaluation",
    },
    "submit_access_decision": {
        "roles": {"reviewer", "admin"},
        "stage": "manager-approval",
    },
}


def authorize_mcp_invocation(
    session: Session,
    *,
    tool_name: str,
    run_id: str | None,
    stage_id: str | None,
    actor: CurrentUser,
) -> tuple[bool, str]:
    policy = TOOL_POLICY.get(tool_name)
    if not policy:
        return False, "Tool is not registered in the gateway allowlist."
    if not actor.roles.intersection(policy["roles"]):
        return False, "Caller roles do not permit this tool."
    required_stage = policy["stage"]
    if required_stage and (not run_id or stage_id != required_stage):
        return False, f"Tool is restricted to workflow stage {required_stage}."
    if run_id:
        run = session.get(WorkflowRunRecord, run_id)
        if not run:
            return False, "Referenced workflow run does not exist."
        if stage_id not in {stage["stage_id"] for stage in run.stages}:
            return False, "Stage is not declared by the workflow run."
    if tool_name == "submit_access_decision":
        approved_review = session.scalar(
            select(HumanReviewRecord)
            .where(HumanReviewRecord.run_id == run_id)
            .where(HumanReviewRecord.stage_id == stage_id)
            .where(HumanReviewRecord.status == "approved")
        )
        if not approved_review:
            return False, "An approved human review is required before this tool."
    return True, "Allowed by gateway policy."


def record_mcp_invocation(
    session: Session,
    *,
    request_id: str,
    server_asset_id: str,
    tool_name: str,
    run_id: str | None,
    stage_id: str | None,
    actor: CurrentUser,
    decision: str,
    reason: str,
    arguments: dict,
    result: dict | None,
) -> McpInvocationRecord:
    record = McpInvocationRecord(
        request_id=request_id,
        server_asset_id=server_asset_id,
        tool_name=tool_name,
        run_id=run_id,
        stage_id=stage_id,
        actor_email=actor.email,
        decision=decision,
        reason=reason,
        arguments=arguments,
        result=result,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def list_mcp_invocations(session: Session) -> list[McpInvocationView]:
    records = session.scalars(
        select(McpInvocationRecord)
        .order_by(McpInvocationRecord.created_at.desc())
        .limit(100)
    ).all()
    return [McpInvocationView.model_validate(record) for record in records]
