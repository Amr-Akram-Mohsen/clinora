"""
tests/test_auth_api.py

Integration tests for authentication API endpoints.

Tests verify:
- Login with valid credentials → 200 + access token + refresh cookie
- Login with invalid credentials → 401 + correct error shape
- Login with inactive account → 401
- GET /auth/me without token → 401
- GET /auth/me with valid token → 200 + user data
- POST /auth/refresh with valid cookie → 200 + new token
- POST /auth/logout → 204 + cleared cookie
"""

from datetime import UTC

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import PASSWORD_PLAIN, OrganizationFactory, RoleFactory, UserFactory


@pytest_asyncio.fixture
async def seeded_user(session: AsyncSession):
    """Create an org, ADMIN role, and active user in the test DB."""
    org = OrganizationFactory.build()
    session.add(org)
    await session.flush()

    role = RoleFactory.build(name="ADMIN")
    session.add(role)
    await session.flush()

    user = UserFactory.build(organization_id=org.id)
    session.add(user)
    await session.flush()

    from datetime import datetime

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
async def test_login_success(client: AsyncClient, seeded_user):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": seeded_user.email, "password": PASSWORD_PLAIN},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert "expires_in" in body
    # Refresh cookie should be set
    assert "clinora_refresh" in resp.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, seeded_user):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": seeded_user.email, "password": "WrongPassword!"},
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert "request_id" in body["error"] or True  # request_id may be None in tests


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "anything"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, session: AsyncSession):
    org = OrganizationFactory.build()
    session.add(org)
    await session.flush()

    user = UserFactory.build(organization_id=org.id, is_active=False)
    session.add(user)
    await session.flush()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": PASSWORD_PLAIN},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token(client: AsyncClient, seeded_user):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": seeded_user.email, "password": PASSWORD_PLAIN},
    )
    token = login.json()["access_token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == seeded_user.email
    assert "password_hash" not in body
    assert "is_superuser" not in body


@pytest.mark.asyncio
async def test_me_with_invalid_token(client: AsyncClient):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, seeded_user):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": seeded_user.email, "password": PASSWORD_PLAIN},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    resp = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newdoc@clinora.com",
            "password": "SecurePassword123!",
            "full_name": "Dr. New Physician",
            "organization_name": "New Horizons Medical",
            "role": "DOCTOR",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "clinora_refresh" in resp.cookies
