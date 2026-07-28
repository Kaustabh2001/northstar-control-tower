from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import CurrentUser, require_roles
from ..database import get_session
from ..agents.service import get_agent_detail
from ..schemas import AgentDetailResponse

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get(
    "/{asset_id}/versions/{version}",
    response_model=AgentDetailResponse,
)
def get_agent_version_detail(
    asset_id: str,
    version: str,
    session: Session = Depends(get_session),
    _user: CurrentUser = Depends(require_roles("viewer")),
) -> AgentDetailResponse:
    detail = get_agent_detail(session, asset_id, version)
    if not detail:
        raise HTTPException(status_code=404, detail="Agent detail record not found.")
    return detail
