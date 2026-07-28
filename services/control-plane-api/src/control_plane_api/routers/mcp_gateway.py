import os
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import CurrentUser, get_current_user, require_roles
from ..database import get_session
from ..mcp_gateway.client import invoke_mcp_tool
from ..mcp_gateway.policy import authorize_mcp_invocation
from ..mcp_gateway.service import (
    list_mcp_invocations,
    record_mcp_invocation,
)
from ..schemas import (
    McpInvocationView,
    McpToolInvocationRequest,
    McpToolInvocationResponse,
)

router = APIRouter(prefix="/api/v1/mcp-gateway", tags=["mcp-gateway"])


@router.get("/invocations", response_model=list[McpInvocationView])
def get_mcp_invocations(
    session: Session = Depends(get_session),
    _user: CurrentUser = Depends(require_roles("viewer")),
) -> list[McpInvocationView]:
    return list_mcp_invocations(session)


@router.post("/invoke", response_model=McpToolInvocationResponse)
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
