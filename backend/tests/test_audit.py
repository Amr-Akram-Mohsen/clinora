"""
tests/test_audit.py

Tests for audit event generation.

Verifies that important auth actions produce correct audit records.
"""

import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.auth.auth_service import AuthService, RequestContext
from core.errors import AuthenticationError
from infrastructure.database.models.audit import AuditLog
from tests.factories import PASSWORD_PLAIN, OrganizationFactory, RoleFactory, UserFactory

_CTX = RequestContext(
    request_id=uuid.uuid4(),
    ip_address="10.0.0.1",
    user_agent="test-agent",
)


@pytest_asyncio.fixture
async def org_and_user(session: AsyncSession):
    org = OrganizationFactory.build()
    session.add(org)
    await session.flush()

    role = RoleFactory.build(name="ADMIN")
    session.add(role)
    await session.flush()

    user = UserFactory.build(organization_id=org.id)
    session.add(user)
    await session.flush()

    from infrastructure.database.models.user import UserRole
    session.add(UserRole(
        user_id=user.id,
        role_id=role.id,
        assigned_at=datetime.now(tz=UTC),
    ))
    await session.flush()

    return org, user


@pytest.mark.asyncio
async def test_login_success_creates_audit_event(session: AsyncSession, org_and_user):
    org, user = org_and_user
    service = AuthService(session)
    await service.authenticate_user(user.email, PASSWORD_PLAIN, _CTX)

    result = await session.execute(
        select(AuditLog)
        .where(AuditLog.action == "user.login.success")
        .where(AuditLog.actor_id == user.id)
    )
    log = result.scalar_one_or_none()
    assert log is not None
    assert log.outcome == "success"
    assert log.organization_id == org.id


@pytest.mark.asyncio
async def test_login_failure_creates_audit_event(session: AsyncSession, org_and_user):
    org, user = org_and_user
    service = AuthService(session)

    with pytest.raises(AuthenticationError):
        await service.authenticate_user(user.email, "WrongPass!", _CTX)

    result = await session.execute(
        select(AuditLog)
        .where(AuditLog.action == "user.login.failure")
        .where(AuditLog.actor_email == user.email)
    )
    log = result.scalar_one_or_none()
    assert log is not None
    assert log.outcome == "failure"
    # Sensitive data must not appear in audit metadata
    assert "password" not in str(log.metadata_)
    assert "hash" not in str(log.metadata_)


@pytest.mark.asyncio
async def test_logout_creates_audit_event(session: AsyncSession, org_and_user):
    org, user = org_and_user
    service = AuthService(session)

    result_auth = await service.authenticate_user(user.email, PASSWORD_PLAIN, _CTX)
    await service.revoke_session(result_auth.refresh_token, user, _CTX)

    result = await session.execute(
        select(AuditLog)
        .where(AuditLog.action == "user.logout")
        .where(AuditLog.actor_id == user.id)
    )
    log = result.scalar_one_or_none()
    assert log is not None
    assert log.outcome == "success"
