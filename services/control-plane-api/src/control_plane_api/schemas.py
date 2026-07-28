from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from northstar_contracts import AssetRegistration, GovernanceState

from .auth import CurrentUser


class AssetResponse(AssetRegistration):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
        str_strip_whitespace=True,
    )

    created_at: datetime
    updated_at: datetime


class DashboardSummary(BaseModel):
    total_assets: int
    managed_assets: int
    discovered_assets: int
    awaiting_review: int
    high_risk_assets: int
    by_type: dict[str, int]
    model_provider: str = "not_configured"


class AgentSkill(BaseModel):
    skill_id: str
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    input_modes: list[str] = Field(default_factory=list)
    output_modes: list[str] = Field(default_factory=list)


class AgentCardView(BaseModel):
    name: str
    description: str
    protocol_version: str
    url: str
    preferred_transport: str
    capabilities: dict[str, bool]
    skills: list[AgentSkill]


class AssetDependency(BaseModel):
    asset_id: str
    version: str
    relationship: str
    display_name: str
    asset_type: str


class GovernanceControl(BaseModel):
    control_id: str
    name: str
    status: str
    evidence: str


class AgentHealth(BaseModel):
    status: str
    latency_ms: int | None
    last_checked_at: datetime | None


class AuditEvent(BaseModel):
    event_id: str
    action: str
    actor_email: str
    detail: str
    created_at: datetime


class AgentDetailResponse(BaseModel):
    asset: AssetResponse
    agent_card: AgentCardView
    dependencies: list[AssetDependency]
    controls: list[GovernanceControl]
    health: AgentHealth
    version_history: list[AssetResponse]
    audit_events: list[AuditEvent]
    runtime_connected: bool = False


class AssetDetailResponse(BaseModel):
    asset: AssetResponse
    detail_kind: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    version_history: list[AssetResponse] = Field(default_factory=list)
    audit_events: list[AuditEvent] = Field(default_factory=list)
    live_status: dict[str, Any] | None = None


class GovernanceEvidence(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_id: str
    asset_id: str
    version: str
    evidence_type: str
    title: str
    status: str
    reference: str
    collected_by: str
    created_at: datetime


class GovernanceApproval(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    approval_id: str
    asset_id: str
    version: str
    display_name: str
    asset_type: str
    current_state: str
    target_state: str
    status: str
    requested_by: str
    request_note: str
    decided_by: str | None
    decision_note: str | None
    created_at: datetime
    decided_at: datetime | None


class GovernancePortfolio(BaseModel):
    approvals: list[GovernanceApproval]
    evidence: list[GovernanceEvidence]
    state_counts: dict[str, int]
    allowed_transitions: dict[str, list[str]]


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
    note: str = Field(min_length=3, max_length=500)


class RuntimeStage(BaseModel):
    stage_id: str
    display_name: str
    status: str
    kind: str
    started_at: str | None = None
    completed_at: str | None = None
    attempt: int = 1
    summary: str | None = None


class WorkflowRunView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    workflow_asset_id: str
    workflow_version: str
    workflow_name: str
    status: str
    current_stage_id: str | None
    correlation: dict[str, Any]
    stages: list[RuntimeStage]
    checkpoint_ref: str | None
    error_code: str | None
    error_summary: str | None
    started_at: datetime
    updated_at: datetime


class RuntimeEventView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    run_id: str
    event_type: str
    stage_id: str | None
    actor_id: str
    payload: dict[str, Any]
    occurred_at: datetime


class HumanReviewView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_id: str
    run_id: str
    stage_id: str
    title: str
    reason: str
    policy_evidence: list[str]
    requested_action: dict[str, Any]
    status: str
    requested_at: datetime
    expires_at: datetime
    decided_by: str | None
    decision: str | None
    rationale: str | None
    decided_at: datetime | None


class RuntimePortfolio(BaseModel):
    runs: list[WorkflowRunView]
    reviews: list[HumanReviewView]
    status_counts: dict[str, int]


class RunDetailResponse(BaseModel):
    run: WorkflowRunView
    events: list[RuntimeEventView]
    review: HumanReviewView | None = None


class HumanReviewDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approve|reject|request_changes)$")
    rationale: str = Field(min_length=3, max_length=500)


class DummyRunRequest(BaseModel):
    request_id: str = Field(min_length=3, max_length=80)
    requester: str = Field(min_length=2, max_length=120)
    application: str = Field(min_length=2, max_length=120)
    entitlement: str = Field(min_length=2, max_length=160)


class EmergencyLifecycleRequest(BaseModel):
    action: str = Field(pattern="^(suspend|rollback)$")
    reason: str = Field(min_length=8, max_length=500)
    target_version: str | None = Field(default=None, max_length=80)


class McpToolInvocationRequest(BaseModel):
    server_asset_id: str = "mcp.keycloak"
    server_version: str = "0.2.0"
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    run_id: str | None = None
    stage_id: str | None = None


class McpToolInvocationResponse(BaseModel):
    request_id: str
    decision: str
    reason: str
    result: dict[str, Any] | None = None


class McpInvocationView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    request_id: str
    server_asset_id: str
    tool_name: str
    run_id: str | None
    stage_id: str | None
    actor_email: str
    decision: str
    reason: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None
    created_at: datetime


class GovernanceTransitionRequest(BaseModel):
    target_state: GovernanceState
    note: str = Field(min_length=3, max_length=500)


class SessionResponse(CurrentUser):
    auth_mode: str

