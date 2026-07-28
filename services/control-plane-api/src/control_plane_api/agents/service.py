from sqlalchemy import select
from sqlalchemy.orm import Session

from northstar_contracts import AssetType

from ..models import AgentDetailRecord, AssetRecord, AuditEventRecord
from ..registry.service import to_response
from ..schemas import (
    AgentCardView,
    AgentDetailResponse,
    AgentHealth,
    AssetDependency,
    AuditEvent,
    GovernanceControl,
)


def get_agent_detail(
    session: Session,
    asset_id: str,
    version: str,
) -> AgentDetailResponse | None:
    asset_record = session.get(AssetRecord, (asset_id, version))
    detail = session.get(AgentDetailRecord, (asset_id, version))
    if (
        not asset_record
        or asset_record.asset_type != AssetType.AGENT.value
        or not detail
    ):
        return None
    versions = session.scalars(
        select(AssetRecord)
        .where(AssetRecord.asset_id == asset_id)
        .order_by(AssetRecord.created_at.desc())
    )
    audit_records = session.scalars(
        select(AuditEventRecord)
        .where(AuditEventRecord.asset_id == asset_id)
        .where(AuditEventRecord.version == version)
        .order_by(AuditEventRecord.created_at.desc())
        .limit(20)
    )
    return AgentDetailResponse(
        asset=to_response(asset_record),
        agent_card=AgentCardView.model_validate(detail.agent_card),
        dependencies=[
            AssetDependency.model_validate(item) for item in detail.dependencies
        ],
        controls=[GovernanceControl.model_validate(item) for item in detail.controls],
        health=AgentHealth(
            status=detail.health_status,
            latency_ms=detail.health_latency_ms,
            last_checked_at=detail.last_checked_at,
        ),
        version_history=[to_response(item) for item in versions],
        audit_events=[
            AuditEvent.model_validate(item, from_attributes=True)
            for item in audit_records
        ],
    )
