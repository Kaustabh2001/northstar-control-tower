from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class AssetRecord(Base):
    __tablename__ = "assets"

    asset_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    version: Mapped[str] = mapped_column(String(80), primary_key=True)
    asset_type: Mapped[str] = mapped_column(String(40), index=True)
    display_name: Mapped[str] = mapped_column(String(240), index=True)
    owner: Mapped[str] = mapped_column(String(180), index=True)
    intended_use: Mapped[str] = mapped_column(Text)
    prohibited_uses: Mapped[list[str]] = mapped_column(JSON, default=list)
    governance_state: Mapped[str] = mapped_column(String(40), index=True)
    risk_level: Mapped[str] = mapped_column(String(30), index=True)
    source_commit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    labels: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class AgentDetailRecord(Base):
    __tablename__ = "agent_details"

    asset_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    version: Mapped[str] = mapped_column(String(80), primary_key=True)
    agent_card: Mapped[dict] = mapped_column(JSON)
    dependencies: Mapped[list[dict]] = mapped_column(JSON, default=list)
    controls: Mapped[list[dict]] = mapped_column(JSON, default=list)
    health_status: Mapped[str] = mapped_column(String(30), default="not_checked")
    health_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class AssetDetailRecord(Base):
    __tablename__ = "asset_details"

    asset_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    version: Mapped[str] = mapped_column(String(80), primary_key=True)
    detail_kind: Mapped[str] = mapped_column(String(40), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class AuditEventRecord(Base):
    __tablename__ = "audit_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    asset_id: Mapped[str] = mapped_column(String(120), index=True)
    version: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(80))
    actor_subject: Mapped[str] = mapped_column(String(180))
    actor_email: Mapped[str] = mapped_column(String(240))
    detail: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class GovernanceEvidenceRecord(Base):
    __tablename__ = "governance_evidence"

    evidence_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    asset_id: Mapped[str] = mapped_column(String(120), index=True)
    version: Mapped[str] = mapped_column(String(80))
    evidence_type: Mapped[str] = mapped_column(String(60), index=True)
    title: Mapped[str] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(30), default="accepted")
    reference: Mapped[str] = mapped_column(Text)
    collected_by: Mapped[str] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class GovernanceApprovalRecord(Base):
    __tablename__ = "governance_approvals"

    approval_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    asset_id: Mapped[str] = mapped_column(String(120), index=True)
    version: Mapped[str] = mapped_column(String(80))
    target_state: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), index=True, default="pending")
    requested_by: Mapped[str] = mapped_column(String(240))
    request_note: Mapped[str] = mapped_column(Text)
    decided_by: Mapped[str | None] = mapped_column(String(240), nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkflowRunRecord(Base):
    __tablename__ = "workflow_runs"

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_asset_id: Mapped[str] = mapped_column(String(120), index=True)
    workflow_version: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), index=True)
    current_stage_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    correlation: Mapped[dict] = mapped_column(JSON, default=dict)
    stages: Mapped[list[dict]] = mapped_column(JSON, default=list)
    checkpoint_ref: Mapped[str | None] = mapped_column(String(240), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class RuntimeEventRecord(Base):
    __tablename__ = "runtime_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    stage_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    actor_id: Mapped[str] = mapped_column(String(180))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class HumanReviewRecord(Base):
    __tablename__ = "human_reviews"

    review_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    stage_id: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(240))
    reason: Mapped[str] = mapped_column(Text)
    policy_evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    requested_action: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), index=True, default="pending")
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    decided_by: Mapped[str | None] = mapped_column(String(240), nullable=True)
    decision: Mapped[str | None] = mapped_column(String(40), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class McpInvocationRecord(Base):
    __tablename__ = "mcp_invocations"

    request_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    server_asset_id: Mapped[str] = mapped_column(String(120), index=True)
    tool_name: Mapped[str] = mapped_column(String(160), index=True)
    run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    stage_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    actor_email: Mapped[str] = mapped_column(String(240))
    decision: Mapped[str] = mapped_column(String(30), index=True)
    reason: Mapped[str] = mapped_column(Text)
    arguments: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

