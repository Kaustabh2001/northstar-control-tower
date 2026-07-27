from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, String, Text
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

