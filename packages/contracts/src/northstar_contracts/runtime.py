from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from .assets import AssetRef
from .base import ContractModel, Identifier, NonEmptyString, utc_now
from .enums import ReviewDecision, RunStatus, RuntimeEventType


class CorrelationIds(ContractModel):
    trace_id: NonEmptyString
    langgraph_thread_id: NonEmptyString
    langfuse_trace_id: NonEmptyString | None = None
    a2a_task_ids: list[NonEmptyString] = Field(default_factory=list)
    mcp_request_ids: list[NonEmptyString] = Field(default_factory=list)


class WorkflowRun(ContractModel):
    run_id: UUID
    workflow: AssetRef
    status: RunStatus
    current_stage_id: Identifier | None = None
    correlation: CorrelationIds
    started_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    checkpoint_ref: NonEmptyString | None = None
    error_code: NonEmptyString | None = None
    error_summary: NonEmptyString | None = None

    @model_validator(mode="after")
    def validate_failure_details(self) -> "WorkflowRun":
        if self.status == RunStatus.FAILED and not self.error_code:
            raise ValueError("failed workflow runs require error_code")
        return self


class HumanReviewRequest(ContractModel):
    review_id: UUID
    run_id: UUID
    stage_id: Identifier
    title: NonEmptyString
    reason: NonEmptyString
    policy_evidence: list[NonEmptyString] = Field(min_length=1)
    requested_action: dict[str, Any]
    requested_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime

    @model_validator(mode="after")
    def validate_expiry(self) -> "HumanReviewRequest":
        if self.expires_at <= self.requested_at:
            raise ValueError("human review expires_at must be after requested_at")
        return self


class HumanReviewDecision(ContractModel):
    review_id: UUID
    run_id: UUID
    decision: ReviewDecision
    decided_by: NonEmptyString
    rationale: NonEmptyString
    decided_at: datetime = Field(default_factory=utc_now)


class RuntimeEvent(ContractModel):
    event_id: UUID
    event_type: RuntimeEventType
    run_id: UUID
    workflow: AssetRef
    occurred_at: datetime = Field(default_factory=utc_now)
    correlation: CorrelationIds
    stage_id: Identifier | None = None
    actor_id: NonEmptyString
    payload: dict[str, Any] = Field(default_factory=dict)
    schema_version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")

