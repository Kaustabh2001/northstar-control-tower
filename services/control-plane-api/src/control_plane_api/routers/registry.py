import os

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from northstar_contracts import AssetRegistration, AssetType, GovernanceState

from ..auth import CurrentUser, require_roles
from ..database import get_session
from ..mcp_gateway.client import discover_mcp_server
from ..registry.service import (
    create_asset,
    dashboard_summary,
    get_asset,
    get_asset_detail,
    list_assets,
)
from ..schemas import AssetDetailResponse, AssetResponse, DashboardSummary

router = APIRouter(prefix="/api/v1")


@router.get("/dashboard", response_model=DashboardSummary, tags=["dashboard"])
def get_dashboard(
    session: Session = Depends(get_session),
    _user: CurrentUser = Depends(require_roles("viewer")),
) -> DashboardSummary:
    return dashboard_summary(session)


@router.get("/assets", response_model=list[AssetResponse], tags=["registry"])
def get_assets(
    asset_type: AssetType | None = None,
    governance_state: GovernanceState | None = None,
    query: str | None = Query(default=None, max_length=120),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
    _user: CurrentUser = Depends(require_roles("viewer")),
) -> list[AssetResponse]:
    return list_assets(
        session,
        asset_type=asset_type,
        governance_state=governance_state,
        query=query,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/assets",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["registry"],
)
def register_asset(
    asset: AssetRegistration,
    session: Session = Depends(get_session),
    user: CurrentUser = Depends(require_roles("operator", "admin")),
) -> AssetResponse:
    try:
        return create_asset(session, asset, actor=user)
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This asset version is already registered.",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error


@router.get(
    "/assets/{asset_id}/versions/{version}",
    response_model=AssetResponse,
    tags=["registry"],
)
def get_asset_version(
    asset_id: str,
    version: str,
    session: Session = Depends(get_session),
    _user: CurrentUser = Depends(require_roles("viewer")),
) -> AssetResponse:
    asset = get_asset(session, asset_id, version)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset version not found.")
    return asset


@router.get(
    "/assets/{asset_id}/versions/{version}/detail",
    response_model=AssetDetailResponse,
    tags=["registry"],
)
async def get_asset_version_detail(
    asset_id: str,
    version: str,
    refresh_live: bool = False,
    session: Session = Depends(get_session),
    _user: CurrentUser = Depends(require_roles("viewer")),
) -> AssetDetailResponse:
    detail = get_asset_detail(session, asset_id, version)
    if not detail:
        raise HTTPException(status_code=404, detail="Asset detail record not found.")
    if refresh_live and detail.asset.asset_type == AssetType.MCP_SERVER:
        endpoint = os.getenv(
            "NORTHSTAR_FIXTURE_MCP_URL",
            detail.metadata.get("local_endpoint")
            or detail.metadata.get("endpoint", ""),
        )
        if endpoint:
            detail.live_status = await discover_mcp_server(endpoint)
    return detail
