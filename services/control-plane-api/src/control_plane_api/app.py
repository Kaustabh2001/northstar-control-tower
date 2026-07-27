import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from northstar_contracts import AssetRegistration, AssetType, GovernanceState

from .auth import CurrentUser, get_current_user, require_roles
from .database import build_engine, build_session_factory, get_session
from .models import Base
from .repository import (
    create_asset,
    dashboard_summary,
    get_agent_detail,
    get_asset,
    list_assets,
    transition_asset,
)
from .schemas import (
    AgentDetailResponse,
    AssetResponse,
    DashboardSummary,
    GovernanceTransitionRequest,
    SessionResponse,
)
from .seed import seed_demo_assets


def create_app(engine: Engine | None = None, *, seed_demo: bool = True) -> FastAPI:
    database_engine = engine or build_engine()
    session_factory = build_session_factory(database_engine)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        Base.metadata.create_all(database_engine)
        application.state.session_factory = session_factory
        if seed_demo:
            seed_demo_assets(session_factory)
        yield

    application = FastAPI(
        title="Northstar Control Plane",
        version="0.3.0",
        description="Governance API for A2A-ready agentic workflows.",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/healthz", tags=["platform"])
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "mode": os.getenv("NORTHSTAR_AUTH_MODE", "fixture"),
        }

    @application.get(
        "/api/v1/me",
        response_model=SessionResponse,
        tags=["identity"],
    )
    def get_session_identity(
        user: CurrentUser = Depends(get_current_user),
    ) -> SessionResponse:
        return SessionResponse(
            **user.model_dump(),
            auth_mode=os.getenv("NORTHSTAR_AUTH_MODE", "fixture"),
        )

    @application.get(
        "/api/v1/dashboard",
        response_model=DashboardSummary,
        tags=["dashboard"],
    )
    def get_dashboard(
        session: Session = Depends(get_session),
        _user: CurrentUser = Depends(require_roles("viewer")),
    ) -> DashboardSummary:
        return dashboard_summary(session)

    @application.get(
        "/api/v1/assets",
        response_model=list[AssetResponse],
        tags=["registry"],
    )
    def get_assets(
        asset_type: AssetType | None = None,
        governance_state: GovernanceState | None = None,
        query: str | None = Query(default=None, max_length=120),
        session: Session = Depends(get_session),
        _user: CurrentUser = Depends(require_roles("viewer")),
    ) -> list[AssetResponse]:
        return list_assets(
            session,
            asset_type=asset_type,
            governance_state=governance_state,
            query=query,
        )

    @application.post(
        "/api/v1/assets",
        response_model=AssetResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["registry"],
    )
    def register_asset(
        asset: AssetRegistration,
        session: Session = Depends(get_session),
        _user: CurrentUser = Depends(require_roles("operator", "admin")),
    ) -> AssetResponse:
        try:
            return create_asset(session, asset)
        except IntegrityError as error:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This asset version is already registered.",
            ) from error

    @application.get(
        "/api/v1/assets/{asset_id}/versions/{version}",
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset version not found.",
            )
        return asset

    @application.get(
        "/api/v1/agents/{asset_id}/versions/{version}",
        response_model=AgentDetailResponse,
        tags=["agents"],
    )
    def get_agent_version_detail(
        asset_id: str,
        version: str,
        session: Session = Depends(get_session),
        _user: CurrentUser = Depends(require_roles("viewer")),
    ) -> AgentDetailResponse:
        detail = get_agent_detail(session, asset_id, version)
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent detail record not found.",
            )
        return detail

    @application.post(
        "/api/v1/agents/{asset_id}/versions/{version}/governance-state",
        response_model=AgentDetailResponse,
        tags=["agents"],
    )
    def change_agent_governance_state(
        asset_id: str,
        version: str,
        transition: GovernanceTransitionRequest,
        session: Session = Depends(get_session),
        user: CurrentUser = Depends(get_current_user),
    ) -> AgentDetailResponse:
        allowed_roles = {
            GovernanceState.STEWARD_REVIEW: {"operator", "admin"},
            GovernanceState.SHADOW: {"reviewer", "admin"},
            GovernanceState.SUSPENDED: {"reviewer", "admin"},
            GovernanceState.RETIRED: {"admin"},
        }
        required = allowed_roles.get(transition.target_state)
        if not required:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="This transition is not exposed through the portal.",
            )
        if not user.roles.intersection(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of these roles: {', '.join(sorted(required))}.",
            )
        detail = transition_asset(
            session,
            asset_id=asset_id,
            version=version,
            target_state=transition.target_state,
            note=transition.note,
            actor=user,
        )
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent detail record not found.",
            )
        return detail

    return application

