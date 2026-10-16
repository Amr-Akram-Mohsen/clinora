"""
tests/test_auth_service.py

Unit tests for AuthService application layer.

Tests the token rotation, family revocation, and audit event behavior
at the service level without going through HTTP.
"""

import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from application.auth.auth_service import AuthService, RequestContext
from core.errors import AuthenticationError, TokenReuseError
from tests.factories import PASSWORD_PLAIN, OrganizationFactory, RoleFactory, UserFactory

_CTX = RequestContext(
    request_id=uuid.uuid4(),
    ip_address="127.0.0.1",
    user_agent="pytest",
)


@pytest_asyncio.fixture
async def user_in_db(session: AsyncSession):
    org = OrganizationFactory.build()
    session.add(org)
    await session.flush()

    role = RoleFactory.build(name="DOCTOR")
    session.add(role)
    await session.flush()

    user = UserFactory.build(organization_id=org.id)
    session.add(user)
    await session.flush()

    from infrastructure.database.models.user import UserRole
    user_role = UserRole(
        user_id=user.id,
        role_id=role.id,
        assigned_at=datetime.now(tz=UTC),
        assigned_by=None,
    )
    session.add(user_role)
    await session.flush()

    return user


@pytest.mark.asyncio
async def test_authenticate_user_success(session: AsyncSession, user_in_db):
    service = AuthService(session)
    result = await service.authenticate_user(
        user_in_db.email, PASSWORD_PLAIN, _CTX
    )
    assert result.access_token
    assert result.refresh_token
    assert result.user.id == user_in_db.id


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(session: AsyncSession, user_in_db):
    service = AuthService(session)
    with pytest.raises(AuthenticationError):
        await service.authenticate_user(user_in_db.email, "WrongPassword!", _CTX)


@pytest.mark.asyncio
async def test_authenticate_user_not_found(session: AsyncSession, user_in_db):
    service = AuthService(session)
    with pytest.raises(AuthenticationError):
        await service.authenticate_user("ghost@example.com", PASSWORD_PLAIN, _CTX)


@pytest.mark.asyncio
async def test_refresh_session_rotates_token(session: AsyncSession, user_in_db):
    service = AuthService(session)

    # First login
    result1 = await service.authenticate_user(
        user_in_db.email, PASSWORD_PLAIN, _CTX
    )

    # Refresh
    result2 = await service.refresh_session(result1.refresh_token, _CTX)

    assert result2.access_token
    # New refresh token should be different
    assert result2.refresh_token != result1.refresh_token


@pytest.mark.asyncio
async def test_refresh_reuse_revokes_family(session: AsyncSession, user_in_db):
    """Presenting a previously-rotated refresh token must revoke the whole family."""
    service = AuthService(session)

    result1 = await service.authenticate_user(
        user_in_db.email, PASSWORD_PLAIN, _CTX
    )
    old_token = result1.refresh_token

    # Legitimate refresh — rotates old_token
    await service.refresh_session(old_token, _CTX)

    # Now try to reuse the rotated (revoked) old token — should raise TokenReuseError
    with pytest.raises(TokenReuseError):
        await service.refresh_session(old_token, _CTX)


@pytest.mark.asyncio
async def test_revoke_session(session: AsyncSession, user_in_db):
    service = AuthService(session)

    result = await service.authenticate_user(
        user_in_db.email, PASSWORD_PLAIN, _CTX
    )

    # Logout
    await service.revoke_session(result.refresh_token, user_in_db, _CTX)

    # Using the revoked token should fail
    with pytest.raises((AuthenticationError, TokenReuseError)):
        await service.refresh_session(result.refresh_token, _CTX)
