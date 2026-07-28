from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from northstar_contracts import GovernanceState

from ..auth import CurrentUser, get_current_user, require_roles
from ..database import get_session
from ..agents.service import get_agent_detail, transition_asset
from ..schemas import AgentDetailResponse, GovernanceTransitionRequest

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


@router.post(
    "/{asset_id}/versions/{version}/governance-state",
    response_model=AgentDetailResponse,
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
        raise HTTPException(status_code=404, detail="Agent detail record not found.")
    return detail
