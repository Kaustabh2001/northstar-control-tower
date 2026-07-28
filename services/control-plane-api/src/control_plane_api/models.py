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

