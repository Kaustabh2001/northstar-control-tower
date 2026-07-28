from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..models import HumanReviewRecord, RuntimeEventRecord, WorkflowRunRecord
from ..schemas import (
    HumanReviewView,
    RuntimeEventView,
    RuntimePortfolio,
    RuntimeStage,
    RunDetailResponse,
    WorkflowRunView,
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
