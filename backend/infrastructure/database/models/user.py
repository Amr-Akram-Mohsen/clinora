"""
infrastructure/database/models/user.py

ORM models: User, Role, UserRole, RefreshToken.

Design notes:
- Users belong to exactly one Organization (tenancy boundary).
- is_superuser is a platform-level flag (future platform admin), distinct
  from application-level roles (ADMIN, DOCTOR, NURSE, RECEPTIONIST).
- Roles are configuration-level records seeded at startup.
- UserRole is the many-to-many join with attribution (who assigned, when).
- RefreshToken implements family-based rotation:
    - Every new token carries a family_id (UUID).
    - A reused revoked token triggers revocation of the entire family.
    - replaced_by tracks the rotation chain for audit purposes.
- Refresh token hashes are SHA-256 of the raw token (see core/security.py).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.base import Base, TimestampMixin, UUIDPKMixin


class Role(UUIDPKMixin, Base):
    """
    Application role (ADMIN, DOCTOR, NURSE, RECEPTIONIST).
    Roles are configuration, not events — no timestamps needed.
    """

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role name={self.name!r}>"


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    __table_args__ = (
        Index("ix_users_organization_id", "organization_id"),
        # email is already unique — the unique constraint creates an index
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Platform-level superuser — distinct from application ADMIN role.
    # Only set for system/platform administrators; not used for clinic owners.
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Email verification & Account Activation
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    verification_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Password Recovery
    password_reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    password_reset_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Social / Enterprise Identity (Google OAuth 2.0)
    google_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="users"
    )

    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        foreign_keys="UserRole.user_id",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user"
    )

    @property
    def role_names(self) -> list[str]:
        """Convenience accessor — loads from already-joined user_roles."""
        return [ur.role.name for ur in self.user_roles if ur.role is not None]

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class UserRole(Base):
    """
    Many-to-many association between User and Role with attribution.
    Composite PK (user_id, role_id) prevents duplicate assignments.
    """

    __tablename__ = "user_roles"

    __table_args__ = (
        Index("ix_user_roles_role_id", "role_id"),
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    # Nullable: system seeding may not have an actor
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="user_roles", foreign_keys=[user_id]
    )
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")

    def __repr__(self) -> str:
        return f"<UserRole user={self.user_id} role={self.role_id}>"


class RefreshToken(UUIDPKMixin, Base):
    """
    Persistent refresh token with family-based rotation.

    Security model:
    - The raw token is given to the client only at issuance.
    - Only the SHA-256 hash is stored here (token_hash).
    - Tokens belong to a family (family_id). Reuse of a revoked token
      triggers revocation of the entire family (theft detection).
    - replaced_by links rotation chain: old_token → new_token.
    """

    __tablename__ = "refresh_tokens"

    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_family_id", "family_id"),
        Index("ix_refresh_tokens_expires_at", "expires_at"),
        # token_hash is already unique — the unique constraint creates an index
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    family_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    replaced_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    @property
    def is_valid(self) -> bool:
        """True if the token has not been revoked and is not expired."""

        return (
            self.revoked_at is None
            and self.expires_at > datetime.now(tz=UTC)
        )

    def __repr__(self) -> str:
        return f"<RefreshToken id={self.id} user={self.user_id} valid={self.is_valid}>"


# Keep import here to avoid circular dependency at module load time
from infrastructure.database.models.organization import Organization  # noqa: E402, F401
