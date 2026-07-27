from datetime import datetime

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


class GovernanceTransitionRequest(BaseModel):
    target_state: GovernanceState
    note: str = Field(min_length=3, max_length=500)


class SessionResponse(CurrentUser):
    auth_mode: str

