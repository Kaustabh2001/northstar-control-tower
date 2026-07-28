from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..models import AssetRecord, HumanReviewRecord, RuntimeEventRecord, WorkflowRunRecord
from ..schemas import (
    HumanReviewView,
    RuntimeEventView,
    RuntimePortfolio,
    RuntimeStage,
    RunDetailResponse,
    WorkflowRunView,
    DummyRunRequest,
)


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
    run.current_stage_id = (
        "provision-access" if decision == "approve" else review.stage_id
    )
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


def start_dummy_run(
    session: Session,
    *,
    request: DummyRunRequest,
    actor: CurrentUser,
) -> RunDetailResponse:
    workflow = session.get(AssetRecord, ("workflow.access-request", "0.7.0"))
    if not workflow:
        raise LookupError("Dummy workflow asset is not registered.")
    if workflow.governance_state not in {"shadow", "canary", "production"}:
        raise ValueError(
            "Workflow must be approved for shadow, canary, or production execution."
        )
    run_id = str(uuid4())
    review_id = str(uuid4())
    now = datetime.now(UTC)
    stages = [
        {
            "stage_id": "validate-request",
            "display_name": "Validate request",
            "status": "completed",
            "kind": "deterministic",
            "started_at": now.isoformat(),
            "completed_at": now.isoformat(),
            "attempt": 1,
            "summary": "Required fields accepted by deterministic validation.",
        },
        {
            "stage_id": "policy-evaluation",
            "display_name": "Policy and risk evaluation",
            "status": "completed",
            "kind": "a2a_agent",
            "started_at": now.isoformat(),
            "completed_at": now.isoformat(),
            "attempt": 1,
            "summary": "Dummy A2A response: elevated entitlement requires review.",
        },
        {
            "stage_id": "manager-approval",
            "display_name": "Manager approval",
            "status": "waiting_for_human",
            "kind": "human",
            "started_at": now.isoformat(),
            "completed_at": None,
            "attempt": 1,
            "summary": "Paused at an explicit human checkpoint.",
        },
        {
            "stage_id": "provision-access",
            "display_name": "Provision approved access",
            "status": "pending",
            "kind": "mcp_tool",
            "started_at": None,
            "completed_at": None,
            "attempt": 1,
            "summary": None,
        },
        {
            "stage_id": "close-request",
            "display_name": "Close request",
            "status": "pending",
            "kind": "deterministic",
            "started_at": None,
            "completed_at": None,
            "attempt": 1,
            "summary": None,
        },
    ]
    run = WorkflowRunRecord(
        run_id=run_id,
        workflow_asset_id=workflow.asset_id,
        workflow_version=workflow.version,
        status="waiting_for_human",
        current_stage_id="manager-approval",
        correlation={
            "demo": True,
            "request_id": request.request_id,
            "a2a_agent_card": "/.well-known/agent.json",
            "a2a_task_ids": [f"dummy-a2a-{run_id[:8]}"],
            "mcp_request_ids": [],
        },
        stages=stages,
        checkpoint_ref=f"postgres://checkpoints/{run_id}",
        started_at=now,
        updated_at=now,
    )
    session.add(run)
    session.add(
        HumanReviewRecord(
            review_id=review_id,
            run_id=run_id,
            stage_id="manager-approval",
            title=f"Review {request.application} access",
            reason="Dummy policy evaluation classified this entitlement as elevated.",
            policy_evidence=["DUMMY-POLICY-001", "Synthetic risk score: 72/100"],
            requested_action=request.model_dump(),
            status="pending",
            requested_at=now,
            expires_at=now + timedelta(hours=4),
        )
    )
    for event_type, stage_id, payload in (
        ("run.started", "validate-request", {"demo": True}),
        ("stage.completed", "validate-request", {"validation": "passed"}),
        (
            "stage.completed",
            "policy-evaluation",
            {"transport": "a2a", "result": "human_review_required"},
        ),
        (
            "run.waiting_for_human",
            "manager-approval",
            {"review_id": review_id},
        ),
    ):
        session.add(
            RuntimeEventRecord(
                event_id=str(uuid4()),
                run_id=run_id,
                event_type=event_type,
                stage_id=stage_id,
                actor_id=actor.email,
                payload=payload,
                occurred_at=now,
            )
        )
    session.commit()
    detail = run_detail(session, run_id)
    assert detail is not None
    return detail
