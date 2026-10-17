"""
infrastructure/repositories/user_repository.py

Repository for User and Role persistence queries.

Responsibilities:
- Encapsulate all DB queries related to User and Role.
- Always eager-load user_roles + role so callers never trigger lazy-load.
- Return ORM objects — serialization to API schemas happens in the API layer.

Non-goals:
- Does not enforce business rules (that is the application/domain layer).
- Does not create, rotate, or revoke tokens (see token_repository.py).
- Does not write audit events.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from infrastructure.database.models.organization import Organization
from infrastructure.database.models.user import Role, User, UserRole


class UserRepository:
    """
    Data access for User and Role entities.

    Instantiated per-request with an injected AsyncSession, matching the
    session lifetime managed by get_db_session in infrastructure/database/engine.py.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_email(self, email: str) -> User | None:
        """
        Find an active user by email, eagerly loading their roles.
        Returns None if not found or inactive.
        """
        stmt = (
            select(User)
            .where(User.email == email.lower().strip())
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role)
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        """Find a user by UUID, eagerly loading roles."""
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role)
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_role_by_name(self, name: str) -> Role | None:
        """Find a role by its name (case-sensitive; names are uppercase by convention)."""
        stmt = select(Role).where(Role.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_user(self, user: User) -> User:
        """Persist a new User. Caller is responsible for committing the session."""
        self._session.add(user)
        await self._session.flush()  # Assign DB-generated defaults before returning
        return user

    async def add_role(self, role: Role) -> Role:
        """Persist a new Role. Used during seeding."""
        self._session.add(role)
        await self._session.flush()
        return role

    async def assign_role(self, user_role: UserRole) -> None:
        """Assign a role to a user."""
        self._session.add(user_role)
        await self._session.flush()

    async def find_organization_by_slug(self, slug: str) -> Organization | None:
        """Find an organization by slug."""
        stmt = select(Organization).where(Organization.slug == slug)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_default_organization(self) -> Organization | None:
        """Find first active organization as fallback."""
        stmt = select(Organization).order_by(Organization.created_at.asc()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_organization(self, organization: Organization) -> Organization:
        """Persist a new Organization."""
        self._session.add(organization)
        await self._session.flush()
        return organization

    async def find_by_verification_token(self, token: str) -> User | None:
        """Find an active user by email verification token, eagerly loading roles."""
        stmt = (
            select(User)
            .where(User.verification_token == token)
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role)
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_reset_token(self, token: str) -> User | None:
        """Find an active user by password reset token, eagerly loading roles."""
        stmt = (
            select(User)
            .where(User.password_reset_token == token)
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role)
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_google_id(self, google_id: str) -> User | None:
        """Find a user by their Google OAuth subject ID, eagerly loading roles."""
        stmt = (
            select(User)
            .where(User.google_id == google_id)
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role)
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user(self, user: User) -> User:
        """Flush changes to a modified User entity."""
        await self._session.flush()
        return user
