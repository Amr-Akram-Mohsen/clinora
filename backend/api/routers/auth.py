"""
api/routers/auth.py

Authentication endpoints.

Routes:
- POST /auth/login      — credential login, returns access token, sets refresh cookie
- POST /auth/refresh    — rotate refresh token, returns new access token
- POST /auth/logout     — revoke current refresh token, clear cookie
- GET  /auth/me         — return current user info

Design:
- Refresh tokens are transmitted as HTTP-only, SameSite=Lax cookies to prevent
  XSS theft. Access tokens are returned in the JSON body.
- Route handlers extract HTTP concerns (headers, cookies, request metadata)
  and delegate business logic to AuthService.
- Audit events are written inside AuthService, not in route handlers.
- All responses use explicit Pydantic schemas — ORM objects are never returned raw.
"""

import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Response
from fastapi import status as http_status

from api.deps import (
    ActiveUser,
    DbSession,
    get_refresh_token_from_cookie,
    get_request_context,
)
from api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead
from application.auth.auth_service import AuthService, RequestContext
from core.config import settings
from core.errors import AuthenticationError

router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_NAME = "clinora_refresh"
_COOKIE_MAX_AGE = int(timedelta(days=settings.refresh_token_expire_days).total_seconds())


def _make_request_context(request: Request) -> RequestContext:
    ctx_dict = get_request_context(request)
    request_id = ctx_dict.get("request_id")
    return RequestContext(
        request_id=uuid.UUID(request_id) if request_id else None,
        ip_address=ctx_dict.get("ip_address"),
        user_agent=ctx_dict.get("user_agent"),
    )


def _set_refresh_cookie(response: Response, raw_refresh_token: str) -> None:
    """Set refresh token as HTTP-only cookie."""
    response.set_cookie(
        key=_COOKIE_NAME,
        value=raw_refresh_token,
        max_age=_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,  # HTTPS-only in production
        path="/auth",  # Restrict cookie scope to /auth routes
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_COOKIE_NAME, path="/auth")


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    session: DbSession,
) -> TokenResponse:
    """
    Register a new user account.
    Returns an access token (JSON body) and sets a refresh token cookie.
    """
    ctx = _make_request_context(request)
    service = AuthService(session)
    result = await service.register_user(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        organization_name=body.organization_name,
        role_name=body.role,
        ctx=ctx,
    )

    _set_refresh_cookie(response, result.refresh_token)

    return TokenResponse(
        access_token=result.access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=http_status.HTTP_200_OK,
)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    session: DbSession,
) -> TokenResponse:
    """
    Authenticate with email and password.
    Returns an access token (JSON body) and sets a refresh token cookie.
    """
    ctx = _make_request_context(request)
    service = AuthService(session)
    result = await service.authenticate_user(body.email, body.password, ctx)

    _set_refresh_cookie(response, result.refresh_token)

    return TokenResponse(
        access_token=result.access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=http_status.HTTP_200_OK,
)
async def refresh(
    request: Request,
    response: Response,
    session: DbSession,
    raw_refresh_token: str | None = Depends(get_refresh_token_from_cookie),
) -> TokenResponse:
    """
    Rotate a refresh token and issue a new access token.
    Refresh token is read from the HTTP-only cookie set during login.
    """
    if not raw_refresh_token:
        raise AuthenticationError("Refresh token cookie is missing")

    ctx = _make_request_context(request)
    service = AuthService(session)
    result = await service.refresh_session(raw_refresh_token, ctx)

    _set_refresh_cookie(response, result.refresh_token)

    return TokenResponse(
        access_token=result.access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/logout",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def logout(
    request: Request,
    response: Response,
    session: DbSession,
    current_user: ActiveUser,
    raw_refresh_token: str | None = Depends(get_refresh_token_from_cookie),
) -> None:
    """
    Revoke the current refresh token and clear the cookie.
    Access token expires naturally (15 min max window).
    """
    ctx = _make_request_context(request)
    service = AuthService(session)

    if raw_refresh_token:
        await service.revoke_session(raw_refresh_token, current_user, ctx)

    _clear_refresh_cookie(response)


@router.get(
    "/me",
    response_model=UserRead,
    status_code=http_status.HTTP_200_OK,
)
async def get_me(current_user: ActiveUser) -> UserRead:
    """Return the authenticated user's profile."""
    return UserRead.from_orm_user(current_user)
