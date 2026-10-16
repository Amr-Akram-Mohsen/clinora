"""
api/schemas/common.py

Shared Pydantic response schemas used across all API routers.

Responsibilities:
- Define the consistent error envelope (ErrorDetail, ErrorResponse).
- Define PaginatedResponse for list endpoints (Phase 2+).
- Define HealthResponse for the health endpoint.

These schemas are the public API contract — they must not expose internal
ORM fields, domain internals, or sensitive data.
"""

from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T")


class FieldErrorDetail(BaseModel):
    field: str
    message: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: UUID | None = None
    details: list[FieldErrorDetail] | None = None


class ErrorResponse(BaseModel):
    """
    Consistent error envelope for all API error responses.

    Example:
        {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "...",
                "request_id": "uuid",
                "details": [{"field": "email", "message": "Invalid format"}]
            }
        }
    """

    error: ErrorDetail


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated list response for collection endpoints.
    Introduced here for future endpoints (Phase 2+).
    """

    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[T]:
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total,
        )


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
