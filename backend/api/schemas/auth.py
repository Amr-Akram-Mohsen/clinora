"""
api/schemas/auth.py

Pydantic request/response schemas for authentication endpoints.

Serialization contract:
- LoginRequest  → POST /auth/login
- TokenResponse → login + refresh responses
- RefreshRequest → POST /auth/refresh (body carries token if not using cookie)
- UserRead      → GET /auth/me

Security:
- password_hash is never included in any response schema.
- is_superuser is internal and not exposed to the frontend.
- The UserRead schema controls exactly what user data crosses the API boundary.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, EmailStr, Field, field_validator

if TYPE_CHECKING:
    from infrastructure.database.models.user import User



class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    organization_name: str | None = Field(default=None, max_length=255)
    role: str = Field(default="DOCTOR", max_length=50)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("full_name", mode="before")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return v.strip()


class TokenResponse(BaseModel):
    """
    Returned on successful login or token refresh.
    The refresh token is set as an HTTP-only cookie by the route handler,
    not included in this JSON body.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires


class UserRoleRead(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class UserRead(BaseModel):
    """
    Public representation of the authenticated user.
    Never exposes password_hash, is_superuser, or internal DB fields.
    """

    id: uuid.UUID
    email: str
    full_name: str
    organization_id: uuid.UUID
    is_active: bool
    roles: list[str]   # Role names list, derived from user_roles
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_user(cls, user: User) -> UserRead:

        """
        Explicit factory from ORM User — avoids implicit orm_mode surprises
        and makes the mapping intentional.
        """
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            organization_id=user.organization_id,
            is_active=user.is_active,
            roles=user.role_names,
            created_at=user.created_at,
        )
