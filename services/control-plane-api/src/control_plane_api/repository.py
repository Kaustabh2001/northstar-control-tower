from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from northstar_contracts import AssetRegistration, AssetType, GovernanceState

from .models import AssetRecord
from .schemas import AssetResponse, DashboardSummary

MANAGED_STATES = {
    state.value
    for state in GovernanceState
    if state not in {GovernanceState.DISCOVERED, GovernanceState.RETIRED}
}


def to_response(record: AssetRecord) -> AssetResponse:
    return AssetResponse.model_validate(record)


def create_asset(session: Session, asset: AssetRegistration) -> AssetResponse:
    record = AssetRecord(**asset.model_dump(mode="json"))
    session.add(record)
    session.commit()
    session.refresh(record)
    return to_response(record)


def get_asset(session: Session, asset_id: str, version: str) -> AssetResponse | None:
    record = session.get(AssetRecord, (asset_id, version))
    return to_response(record) if record else None


def list_assets(
    session: Session,
    *,
    asset_type: AssetType | None = None,
    governance_state: GovernanceState | None = None,
    query: str | None = None,
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
    statement = statement.order_by(AssetRecord.display_name, AssetRecord.version)
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

