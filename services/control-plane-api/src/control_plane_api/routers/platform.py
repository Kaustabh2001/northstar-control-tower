import os

from fastapi import APIRouter, Depends

from ..auth import CurrentUser, get_current_user
from ..schemas import SessionResponse

router = APIRouter(tags=["platform"])


@router.get("/healthz")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "mode": os.getenv("NORTHSTAR_AUTH_MODE", "keycloak"),
    }


@router.get("/api/v1/me", response_model=SessionResponse, tags=["identity"])
def get_session_identity(
    user: CurrentUser = Depends(get_current_user),
) -> SessionResponse:
    return SessionResponse(
        **user.model_dump(),
        auth_mode=os.getenv("NORTHSTAR_AUTH_MODE", "keycloak"),
    )
