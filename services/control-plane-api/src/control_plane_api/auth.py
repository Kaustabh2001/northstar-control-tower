import os
from collections.abc import Callable
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel


class CurrentUser(BaseModel):
    subject: str
    email: str
    display_name: str
    roles: set[str]


security = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "Authentication required.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


@lru_cache(maxsize=1)
def _jwks_client() -> jwt.PyJWKClient:
    issuer = os.getenv(
        "NORTHSTAR_AUTH_ISSUER",
        "http://localhost:8080/realms/northstar",
    )
    jwks_url = os.getenv(
        "NORTHSTAR_AUTH_JWKS_URL",
        f"{issuer}/protocol/openid-connect/certs",
    )
    return jwt.PyJWKClient(jwks_url)


def _fixture_user(token: str) -> CurrentUser:
    role = token.removeprefix("fixture-")
    if role not in {"viewer", "operator", "reviewer", "admin"}:
        raise _unauthorized("Invalid fixture access token.")
    inherited = {"viewer"}
    if role == "operator":
        inherited.add("operator")
    elif role == "reviewer":
        inherited.add("reviewer")
    elif role == "admin":
        inherited.update({"operator", "reviewer", "admin"})
    return CurrentUser(
        subject=f"fixture-{role}",
        email=f"{role}@northstar.local",
        display_name=f"Local {role.title()}",
        roles=inherited,
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security),
    ],
) -> CurrentUser:
    if not credentials:
        raise _unauthorized()

    auth_mode = os.getenv("NORTHSTAR_AUTH_MODE", "fixture")
    if auth_mode == "fixture":
        return _fixture_user(credentials.credentials)

    if auth_mode != "keycloak":
        raise _unauthorized("Unsupported authentication mode.")

    token = credentials.credentials
    issuer = os.getenv(
        "NORTHSTAR_AUTH_ISSUER",
        "http://localhost:8080/realms/northstar",
    )
    audience = os.getenv("NORTHSTAR_AUTH_AUDIENCE", "northstar-api")
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
        )
    except jwt.PyJWTError as error:
        raise _unauthorized("Access token is invalid or expired.") from error

    roles = set(claims.get("realm_access", {}).get("roles", []))
    return CurrentUser(
        subject=claims["sub"],
        email=claims.get("email", claims.get("preferred_username", claims["sub"])),
        display_name=claims.get(
            "name",
            claims.get("preferred_username", "Northstar user"),
        ),
        roles=roles,
    )


CurrentUserDependency = Annotated[CurrentUser, Depends(get_current_user)]


def require_roles(*required_roles: str) -> Callable[[CurrentUserDependency], CurrentUser]:
    def dependency(user: CurrentUserDependency) -> CurrentUser:
        if not user.roles.intersection(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of these roles: {', '.join(required_roles)}.",
            )
        return user

    return dependency
