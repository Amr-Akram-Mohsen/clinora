"""
api/deps.py

FastAPI dependency functions shared across routers.

Responsibilities:
- get_db_session: Re-export the session generator for use in Depends().
- get_current_user: Extract and validate the JWT from Authorization header,
  return the authenticated User ORM object.
- require_active_user: Guard that the user account is active.
- require_roles: Factory for role-based access guards.

These dependencies keep route handlers thin — they handle HTTP extraction
and call the appropriate auth primitive; no business logic lives here.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Cookie, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AuthenticationError, AuthorizationError
from core.security import decode_access_token
from infrastructure.database.engine import get_db_session
from infrastructure.database.models.user import User
from infrastructure.repositories.user_repository import UserRepository

__all__ = [
    "ActiveUser",
    "CurrentUser",
    "DbSession",
    "get_current_user",
    "get_db_session",
    "get_refresh_token_from_cookie",
    "get_request_context",
    "require_active_user",
    "require_roles",
]

# Re-export for routers that use Depends(get_db_session)
DbSession = Annotated[AsyncSession, Depends(get_db_session)]

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    session: DbSession,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ] = None,
) -> User:
    """
    Validate the Bearer access token from the Authorization header.
    Returns the fully-loaded User ORM object (with roles eager-loaded).

    Raises AuthenticationError (→ 401) if token is missing, invalid, or expired.
    """
    if credentials is None:
        raise AuthenticationError("Authorization header is required")

    payload = decode_access_token(credentials.credentials)

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as err:
        raise AuthenticationError("Invalid token payload") from err

    user_repo = UserRepository(session)
    user = await user_repo.find_by_id(user_id)

    if user is None:
        raise AuthenticationError("User not found")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_active_user(current_user: CurrentUser) -> User:
    """Guard: user must be active (not deactivated)."""
    if not current_user.is_active:
        raise AuthorizationError("Account is inactive")
    return current_user


ActiveUser = Annotated[User, Depends(require_active_user)]


def require_roles(*roles: str) -> Callable[[User], Coroutine[Any, Any, User]]:
    """
    Dependency factory: ensure the current user has at least one of the specified roles.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_roles("ADMIN"))])

    Note: is_superuser bypasses role checks (platform admin).
    """

    async def _guard(current_user: ActiveUser) -> User:
        if current_user.is_superuser:
            return current_user
        user_roles = current_user.role_names
        if not any(role in user_roles for role in roles):
            raise AuthorizationError(
                f"Required role(s): {', '.join(roles)}"
            )
        return current_user

    return _guard


def get_request_context(request: Request) -> dict[str, Any]:
    """
    Extract request metadata for audit enrichment.
    Returns a dict with request_id, ip_address, user_agent.
    """
    return {
        "request_id": getattr(request.state, "request_id", None),
        "ip_address": (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or (request.client.host if request.client else None)
        ),
        "user_agent": request.headers.get("User-Agent"),
    }


def get_refresh_token_from_cookie(
    refresh_token: Annotated[str | None, Cookie(alias="clinora_refresh")] = None,
) -> str | None:
    """Extract the refresh token from the HTTP-only cookie."""
    return refresh_token

