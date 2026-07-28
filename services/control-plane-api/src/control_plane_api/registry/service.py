from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from northstar_contracts import AssetRegistration, AssetType, GovernanceState

from ..auth import CurrentUser
from ..models import AssetDetailRecord, AssetRecord, AuditEventRecord
from ..schemas import (
    AssetDetailResponse,
    AssetResponse,
    AuditEvent,
    DashboardSummary,
)

MANAGED_STATES = {
    state.value
    for state in GovernanceState
    if state not in {GovernanceState.DISCOVERED, GovernanceState.RETIRED}
}


def to_response(record: AssetRecord) -> AssetResponse:
    return AssetResponse.model_validate(record)


def create_asset(
    session: Session,
    asset: AssetRegistration,
    *,
    actor: CurrentUser | None = None,
) -> AssetResponse:
    if actor and asset.governance_state not in {
        GovernanceState.DISCOVERED,
        GovernanceState.REGISTERED,
    }:
        raise ValueError(
            "New asset versions must enter through discovered or registered state."
        )
    record = AssetRecord(**asset.model_dump(mode="json"))
    session.add(record)
    if actor:
        session.add(
            AuditEventRecord(
                event_id=str(uuid4()),
                asset_id=asset.asset_id,
                version=asset.version,
                action="registry.asset.registered",
                actor_subject=actor.subject,
                actor_email=actor.email,
                detail=f"Registered {asset.asset_type.value} version {asset.version}.",
            )
        )
    session.commit()
    session.refresh(record)
    return to_response(record)


def get_asset(session: Session, asset_id: str, version: str) -> AssetResponse | None:
    record = session.get(AssetRecord, (asset_id, version))
    return to_response(record) if record else None


def get_asset_detail(
    session: Session,
    asset_id: str,
    version: str,
) -> AssetDetailResponse | None:
    asset_record = session.get(AssetRecord, (asset_id, version))
    if not asset_record:
        return None
    detail = session.get(AssetDetailRecord, (asset_id, version))
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
    return AssetDetailResponse(
        asset=to_response(asset_record),
        detail_kind=detail.detail_kind if detail else asset_record.asset_type,
        metadata=detail.payload if detail else {},
        version_history=[to_response(item) for item in versions],
        audit_events=[
            AuditEvent.model_validate(item, from_attributes=True)
            for item in audit_records
        ],
    )


def list_assets(
    session: Session,
    *,
    asset_type: AssetType | None = None,
    governance_state: GovernanceState | None = None,
    query: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[AssetResponse]:
    statement = select(AssetRecord)
    if asset_type:
        statement = statement.where(AssetRecord.asset_type == asset_type.value)
    if governance_state:
        statement = statement.where(
            AssetRecord.governance_state == governance_state.value
        )
    if query:
        pattern = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                AssetRecord.asset_id.ilike(pattern),
                AssetRecord.display_name.ilike(pattern),
                AssetRecord.owner.ilike(pattern),
            )
        )
    statement = (
        statement.order_by(AssetRecord.display_name, AssetRecord.version)
        .offset(offset)
        .limit(limit)
    )
    return [to_response(record) for record in session.scalars(statement)]


def dashboard_summary(session: Session) -> DashboardSummary:
    by_type = dict(
        session.execute(
            select(AssetRecord.asset_type, func.count()).group_by(
                AssetRecord.asset_type
            )
        ).all()
    )
    states = dict(
        session.execute(
            select(AssetRecord.governance_state, func.count()).group_by(
                AssetRecord.governance_state
            )
        ).all()
    )
    risks = dict(
        session.execute(
            select(AssetRecord.risk_level, func.count()).group_by(
                AssetRecord.risk_level
            )
        ).all()
    )
    return DashboardSummary(
        total_assets=sum(by_type.values()),
        managed_assets=sum(states.get(state, 0) for state in MANAGED_STATES),
        discovered_assets=states.get(GovernanceState.DISCOVERED.value, 0),
        awaiting_review=states.get(GovernanceState.STEWARD_REVIEW.value, 0),
        high_risk_assets=risks.get("high", 0) + risks.get("unacceptable", 0),
        by_type=by_type,
    )
