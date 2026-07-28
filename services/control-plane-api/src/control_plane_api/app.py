import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from northstar_contracts import AssetRegistration, AssetType, GovernanceState

from .auth import CurrentUser, get_current_user, require_roles
from .database import build_engine, build_session_factory, get_session
from .mcp_discovery import discover_mcp_server, invoke_mcp_tool
from .models import Base
from .operations import (
    authorize_mcp_invocation,
    decide_asset_approval,
    decide_human_review,
    governance_portfolio,
    list_mcp_invocations,
    record_mcp_invocation,
    request_asset_approval,
    run_detail,
    runtime_portfolio,
)
from .repository import (
    create_asset,
    dashboard_summary,
    get_agent_detail,
    get_asset,
    get_asset_detail,
    list_assets,
    transition_asset,
)
from .schemas import (
    AgentDetailResponse,
    ApprovalDecisionRequest,
    AssetDetailResponse,
    AssetResponse,
    DashboardSummary,
    GovernanceApproval,
    GovernancePortfolio,
    GovernanceTransitionRequest,
    HumanReviewDecisionRequest,
    McpInvocationView,
    McpToolInvocationRequest,
    McpToolInvocationResponse,
    RunDetailResponse,
    RuntimePortfolio,
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
        version="0.5.0",
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
        "/api/v1/assets/{asset_id}/versions/{version}/detail",
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset detail record not found.",
            )
        if refresh_live and detail.asset.asset_type == AssetType.MCP_SERVER:
            endpoint = os.getenv(
                "NORTHSTAR_FIXTURE_MCP_URL",
                detail.metadata.get("local_endpoint")
                or detail.metadata.get("endpoint", ""),
            )
            if endpoint:
                detail.live_status = await discover_mcp_server(endpoint)
        return detail

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

    @application.get(
        "/api/v1/governance",
        response_model=GovernancePortfolio,
        tags=["governance"],
    )
    def get_governance_portfolio(
        session: Session = Depends(get_session),
        _user: CurrentUser = Depends(require_roles("viewer")),
    ) -> GovernancePortfolio:
        return governance_portfolio(session)

    @application.post(
        "/api/v1/assets/{asset_id}/versions/{version}/approvals",
        response_model=GovernanceApproval,
        status_code=status.HTTP_201_CREATED,
        tags=["governance"],
    )
    def request_governance_approval(
        asset_id: str,
        version: str,
        transition: GovernanceTransitionRequest,
        session: Session = Depends(get_session),
        user: CurrentUser = Depends(require_roles("operator", "admin")),
    ) -> GovernanceApproval:
        try:
            return request_asset_approval(
                session,
                asset_id=asset_id,
                version=version,
                target_state=transition.target_state,
                note=transition.note,
                actor=user,
            )
        except LookupError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @application.post(
        "/api/v1/governance/approvals/{approval_id}/decision",
        response_model=GovernanceApproval,
        tags=["governance"],
    )
    def decide_governance_approval(
        approval_id: str,
        decision: ApprovalDecisionRequest,
        session: Session = Depends(get_session),
        user: CurrentUser = Depends(require_roles("reviewer", "admin")),
    ) -> GovernanceApproval:
        approval = decide_asset_approval(
            session,
            approval_id=approval_id,
            decision=decision.decision,
            note=decision.note,
            actor=user,
        )
        if not approval:
            raise HTTPException(
                status_code=404,
                detail="Pending approval not found.",
            )
        return approval

    @application.get(
        "/api/v1/runtime",
        response_model=RuntimePortfolio,
        tags=["runtime"],
    )
    def get_runtime_portfolio(
        session: Session = Depends(get_session),
        _user: CurrentUser = Depends(require_roles("viewer")),
    ) -> RuntimePortfolio:
        return runtime_portfolio(session)

    @application.get(
        "/api/v1/runtime/runs/{run_id}",
        response_model=RunDetailResponse,
        tags=["runtime"],
    )
    def get_run_detail(
        run_id: str,
        session: Session = Depends(get_session),
        _user: CurrentUser = Depends(require_roles("viewer")),
    ) -> RunDetailResponse:
        detail = run_detail(session, run_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Workflow run not found.")
        return detail

    @application.post(
        "/api/v1/runtime/reviews/{review_id}/decision",
        response_model=RunDetailResponse,
        tags=["runtime"],
    )
    def decide_runtime_review(
        review_id: str,
        decision: HumanReviewDecisionRequest,
        session: Session = Depends(get_session),
        user: CurrentUser = Depends(require_roles("reviewer", "admin")),
    ) -> RunDetailResponse:
        detail = decide_human_review(
            session,
            review_id=review_id,
            decision=decision.decision,
            rationale=decision.rationale,
            actor=user,
        )
        if not detail:
            raise HTTPException(
                status_code=404,
                detail="Pending human review not found.",
            )
        return detail

    @application.get(
        "/api/v1/mcp-gateway/invocations",
        response_model=list[McpInvocationView],
        tags=["mcp-gateway"],
    )
    def get_mcp_invocations(
        session: Session = Depends(get_session),
        _user: CurrentUser = Depends(require_roles("viewer")),
    ) -> list[McpInvocationView]:
        return list_mcp_invocations(session)

    @application.post(
        "/api/v1/mcp-gateway/invoke",
        response_model=McpToolInvocationResponse,
        tags=["mcp-gateway"],
    )
    async def invoke_governed_mcp_tool(
        request: McpToolInvocationRequest,
        session: Session = Depends(get_session),
        user: CurrentUser = Depends(get_current_user),
    ) -> McpToolInvocationResponse:
        request_id = str(uuid4())
        allowed, reason = authorize_mcp_invocation(
            session,
            tool_name=request.tool_name,
            run_id=request.run_id,
            stage_id=request.stage_id,
            actor=user,
        )
        if not allowed:
            record_mcp_invocation(
                session,
                request_id=request_id,
                server_asset_id=request.server_asset_id,
                tool_name=request.tool_name,
                run_id=request.run_id,
                stage_id=request.stage_id,
                actor=user,
                decision="denied",
                reason=reason,
                arguments=request.arguments,
                result=None,
            )
            raise HTTPException(status_code=403, detail=reason)
        endpoint = os.getenv(
            "NORTHSTAR_FIXTURE_MCP_URL",
            "http://localhost:8090/mcp",
        )
        try:
            result = await invoke_mcp_tool(
                endpoint,
                request.tool_name,
                request.arguments,
            )
        except Exception as error:
            reason = f"Upstream MCP call failed: {type(error).__name__}."
            record_mcp_invocation(
                session,
                request_id=request_id,
                server_asset_id=request.server_asset_id,
                tool_name=request.tool_name,
                run_id=request.run_id,
                stage_id=request.stage_id,
                actor=user,
                decision="error",
                reason=reason,
                arguments=request.arguments,
                result=None,
            )
            raise HTTPException(status_code=502, detail=reason) from error
        record_mcp_invocation(
            session,
            request_id=request_id,
            server_asset_id=request.server_asset_id,
            tool_name=request.tool_name,
            run_id=request.run_id,
            stage_id=request.stage_id,
            actor=user,
            decision="allowed",
            reason=reason,
            arguments=request.arguments,
            result=result,
        )
        return McpToolInvocationResponse(
            request_id=request_id,
            decision="allowed",
            reason=reason,
            result=result,
        )

    return application

