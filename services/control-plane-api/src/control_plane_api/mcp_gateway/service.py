from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..models import McpInvocationRecord
from ..schemas import McpInvocationView


def record_mcp_invocation(
    session: Session,
    *,
    request_id: str,
    server_asset_id: str,
    tool_name: str,
    run_id: str | None,
    stage_id: str | None,
    actor: CurrentUser,
    decision: str,
    reason: str,
    arguments: dict,
    result: dict | None,
) -> McpInvocationRecord:
    record = McpInvocationRecord(
        request_id=request_id,
        server_asset_id=server_asset_id,
        tool_name=tool_name,
        run_id=run_id,
        stage_id=stage_id,
        actor_email=actor.email,
        decision=decision,
        reason=reason,
        arguments=arguments,
        result=result,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def list_mcp_invocations(session: Session) -> list[McpInvocationView]:
    records = session.scalars(
        select(McpInvocationRecord)
        .order_by(McpInvocationRecord.created_at.desc())
        .limit(100)
    ).all()
    return [McpInvocationView.model_validate(record) for record in records]
