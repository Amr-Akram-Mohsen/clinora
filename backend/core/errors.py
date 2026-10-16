"""
core/errors.py

Domain exceptions and HTTP error mapping for Clinora.

Responsibilities:
- Define domain-level exceptions that express business/clinical rules.
- Define a consistent API error response structure (ErrorDetail, ErrorResponse).
- Provide an exception handler that maps domain exceptions to HTTP responses.

Design decisions:
- Domain exceptions carry no FastAPI/HTTP concepts — they are pure Python.
- The HTTP mapping lives here (not in route handlers) so that any service layer
  raising a domain exception automatically produces the correct HTTP response.
- All API error bodies conform to the same structure so the frontend has a
  single error-parsing contract.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# Domain exceptions — pure Python, no FastAPI dependency
# ---------------------------------------------------------------------------


class ClinoraDomainError(Exception):
    """Base for all Clinora domain/business exceptions."""


class NotFoundError(ClinoraDomainError):
    """A requested resource does not exist."""

    def __init__(self, resource: str, identifier: Any = None) -> None:
        self.resource = resource
        self.identifier = identifier
        detail = f"{resource} not found"
        if identifier is not None:
            detail += f": {identifier}"
        super().__init__(detail)


class ConflictError(ClinoraDomainError):
    """An operation conflicts with existing state (e.g., duplicate email)."""


class AuthenticationError(ClinoraDomainError):
    """Credentials are invalid or the session cannot be verified."""


class AuthorizationError(ClinoraDomainError):
    """The authenticated user lacks permission for this operation."""


class ValidationError(ClinoraDomainError):
    """
    A business/domain validation rule was violated.
    Distinct from Pydantic schema validation which catches input shape errors.
    """


class TokenReuseError(AuthenticationError):
    """
    A previously revoked refresh token was presented.
    The entire token family is revoked (potential token theft).
    """


# ---------------------------------------------------------------------------
# API error response structure
# ---------------------------------------------------------------------------


class FieldError:
    """A validation error for a specific request field."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message

    def to_dict(self) -> dict[str, str]:
        return {"field": self.field, "message": self.message}


def _error_body(
    code: str,
    message: str,
    request_id: str | None = None,
    details: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if request_id:
        payload["error"]["request_id"] = request_id
    if details:
        payload["error"]["details"] = details
    return payload


def _get_request_id(request: Request) -> str | None:
    return request.state.__dict__.get("request_id")


# ---------------------------------------------------------------------------
# FastAPI exception handlers — registered in api/main.py
# ---------------------------------------------------------------------------


async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=_error_body("NOT_FOUND", str(exc), _get_request_id(request)),
    )


async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=_error_body("CONFLICT", str(exc), _get_request_id(request)),
    )


async def authentication_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=_error_body("AUTHENTICATION_REQUIRED", str(exc), _get_request_id(request)),
        headers={"WWW-Authenticate": "Bearer"},
    )


async def authorization_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=_error_body("FORBIDDEN", str(exc), _get_request_id(request)),
    )


async def domain_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_body("VALIDATION_ERROR", str(exc), _get_request_id(request)),
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected exceptions — hides internal details from clients."""
    from core.logging import get_logger

    logger = get_logger(__name__)
    logger.exception("Unhandled exception", exc_info=exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_body(
            "INTERNAL_ERROR",
            "An unexpected error occurred. Please try again later.",
            _get_request_id(request),
        ),
    )
