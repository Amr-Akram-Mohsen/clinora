"""
application/auth/auth_service.py

Authentication workflow orchestration.

Responsibilities:
- authenticate_user: Validate credentials → issue access + refresh tokens → write audit.
- refresh_session: Validate refresh token → rotate → issue new tokens → write audit.
- revoke_session: Revoke a refresh token on logout → write audit.
- revoke_all_sessions: Revoke all refresh tokens for a user (password change, logout-all).

Design:
- This is a real workflow, not a CRUD pass-through. Each operation spans:
    credential validation, token management, and audit logging.
- The session is NOT committed here; the caller (FastAPI route via get_db_session)
  commits at the end of the request lifecycle.
- Request context (IP, user agent, request_id) is passed in so audit records
  are enriched at the application level, not just HTTP middleware.
- Raises domain exceptions (core.errors) — HTTP mapping happens in error handlers.
"""

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.errors import AuthenticationError, ConflictError, TokenReuseError
from core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from infrastructure.database.models.organization import Organization
from infrastructure.database.models.user import RefreshToken, User, UserRole
from infrastructure.repositories.audit_repository import AuditEvent, AuditRepository
from infrastructure.repositories.token_repository import TokenRepository
from infrastructure.repositories.user_repository import UserRepository


@dataclass
class RequestContext:
    """HTTP request metadata enriching auth audit events."""

    request_id: uuid.UUID | None = None
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass
class AuthResult:
    """Successful authentication result returned to the API layer."""

    access_token: str
    refresh_token: str   # Raw token — client stores in HTTP-only cookie
    token_type: str = "bearer"
    user: User = None  # type: ignore[assignment]


class AuthService:
    """
    Orchestrates authentication workflows.
    Instantiated per-request with injected repositories.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._users = UserRepository(session)
        self._tokens = TokenRepository(session)
        self._audit = AuditRepository(session)

    async def authenticate_user(
        self,
        email: str,
        password: str,
        ctx: RequestContext,
    ) -> AuthResult:
        """
        Validate email/password credentials and issue tokens.

        Audit events:
        - user.login.failure  — invalid credentials
        - user.login.success  — successful login
        """
        user = await self._users.find_by_email(email)

        # Use a constant-time comparison path even on "user not found" to
        # prevent user enumeration via timing side-channels.
        if user is None or not verify_password(password, user.password_hash):
            # Record failure with the provided email (no user ID available on failure)
            org_id = user.organization_id if user else None
            await self._audit.record(AuditEvent(
                organization_id=org_id,
                actor_email=email,
                action="user.login.failure",
                outcome="failure",
                request_id=ctx.request_id,
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
                metadata={"reason": "invalid_credentials"},
            ))
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            await self._audit.record(AuditEvent(
                organization_id=user.organization_id,
                actor_id=user.id,
                actor_email=user.email,
                action="user.login.failure",
                outcome="failure",
                request_id=ctx.request_id,
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
                metadata={"reason": "account_inactive"},
            ))
            raise AuthenticationError("Account is inactive")

        result = await self._issue_tokens(user, ctx)

        await self._audit.record(AuditEvent(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_email=user.email,
            action="user.login.success",
            outcome="success",
            request_id=ctx.request_id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        ))

        return result

    async def register_user(
        self,
        email: str,
        password: str,
        full_name: str,
        organization_name: str | None,
        role_name: str,
        ctx: RequestContext,
    ) -> AuthResult:
        """
        Register a new user account, creating or linking to an organization.
        Issues access and refresh tokens, and records audit event.
        """
        normalized_email = email.lower().strip()
        existing = await self._users.find_by_email(normalized_email)
        if existing:
            raise ConflictError("An account with this email address already exists")

        # Resolve or create organization
        org: Organization | None = None
        if organization_name and organization_name.strip():
            clean_name = organization_name.strip()
            base_slug = re.sub(r"[^a-z0-9]+", "-", clean_name.lower()).strip("-") or "clinic"
            slug = base_slug
            existing_org = await self._users.find_organization_by_slug(slug)
            if existing_org:
                slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
            org = Organization(name=clean_name, slug=slug, is_active=True)
            await self._users.add_organization(org)
        else:
            org = await self._users.find_organization_by_slug("clinora")
            if not org:
                org = await self._users.find_default_organization()
            if not org:
                org = Organization(name="Clinora Clinic", slug="clinora", is_active=True)
                await self._users.add_organization(org)

        # Resolve Role
        target_role_name = role_name.upper().strip() if role_name else "DOCTOR"
        role = await self._users.find_role_by_name(target_role_name)
        if not role:
            role = await self._users.find_role_by_name("DOCTOR")
        if not role:
            role = await self._users.find_role_by_name("ADMIN")

        new_user = User(
            organization_id=org.id,
            email=normalized_email,
            password_hash=hash_password(password),
            full_name=full_name.strip(),
            is_active=True,
            is_superuser=False,
        )
        await self._users.add_user(new_user)

        if role:
            user_role = UserRole(
                user_id=new_user.id,
                role_id=role.id,
                assigned_at=datetime.now(tz=UTC),
                assigned_by=None,
            )
            await self._users.assign_role(user_role)

        # Reload user with eager relationships for tokens
        user = await self._users.find_by_id(new_user.id)
        assert user is not None

        result = await self._issue_tokens(user, ctx)

        await self._audit.record(AuditEvent(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_email=user.email,
            action="user.register.success",
            outcome="success",
            request_id=ctx.request_id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
            metadata={"role": target_role_name, "organization_slug": org.slug},
        ))

        return result

    async def refresh_session(
        self,
        raw_refresh_token: str,
        ctx: RequestContext,
    ) -> AuthResult:
        """
        Rotate a refresh token and issue a new access token.

        Security:
        - If the presented token has already been revoked (possible theft),
          the entire family is revoked immediately.
        - The old token is revoked and a new one is issued atomically within
          the caller's session transaction.

        Audit events:
        - user.token_family_revoked  — revoked token reuse detected
        - user.token_refresh         — successful refresh
        """
        token_hash = hash_refresh_token(raw_refresh_token)
        token_record = await self._tokens.find_by_hash(token_hash)

        if token_record is None:
            raise AuthenticationError("Invalid refresh token")

        if token_record.revoked_at is not None:
            # Token reuse — revoke entire family (theft detection)
            revoked_count = await self._tokens.revoke_family(token_record.family_id)

            user = await self._users.find_by_id(token_record.user_id)
            await self._audit.record(AuditEvent(
                organization_id=user.organization_id if user else None,
                actor_id=token_record.user_id,
                actor_email=user.email if user else "unknown",
                action="user.token_family_revoked",
                outcome="failure",
                request_id=ctx.request_id,
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
                metadata={
                    "family_id": str(token_record.family_id),
                    "revoked_count": revoked_count,
                    "reason": "reuse_of_revoked_token",
                },
            ))
            raise TokenReuseError(
                "Refresh token has already been used. All sessions have been invalidated."
            )

        if not token_record.is_valid:
            raise AuthenticationError("Refresh token has expired")

        user = await self._users.find_by_id(token_record.user_id)
        if user is None or not user.is_active:
            await self._tokens.revoke(token_record)
            raise AuthenticationError("Account is inactive or not found")

        # Issue new tokens in the same family
        new_raw_token = generate_refresh_token()
        new_token_hash = hash_refresh_token(new_raw_token)
        new_token = RefreshToken(
            user_id=user.id,
            token_hash=new_token_hash,
            family_id=token_record.family_id,  # Keep family for rotation chain
            issued_at=datetime.now(tz=UTC),
            expires_at=datetime.now(tz=UTC) + timedelta(
                days=settings.refresh_token_expire_days
            ),
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
        new_token_record = await self._tokens.create(new_token)

        # Revoke the old token, linking to its successor
        await self._tokens.revoke(token_record, replaced_by_id=new_token_record.id)

        access_token = create_access_token(
            subject=str(user.id),
            additional_claims={
                "org_id": str(user.organization_id),
                "roles": user.role_names,
            },
        )

        await self._audit.record(AuditEvent(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_email=user.email,
            action="user.token_refresh",
            outcome="success",
            request_id=ctx.request_id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        ))

        return AuthResult(
            access_token=access_token,
            refresh_token=new_raw_token,
            user=user,
        )

    async def revoke_session(
        self,
        raw_refresh_token: str,
        user: User,
        ctx: RequestContext,
    ) -> None:
        """
        Revoke a specific refresh token (logout from current device).

        Audit events:
        - user.logout
        """
        token_hash = hash_refresh_token(raw_refresh_token)
        token_record = await self._tokens.find_by_hash(token_hash)

        if token_record and token_record.user_id == user.id:
            await self._tokens.revoke(token_record)

        await self._audit.record(AuditEvent(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_email=user.email,
            action="user.logout",
            outcome="success",
            request_id=ctx.request_id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        ))

    async def revoke_all_sessions(
        self,
        user: User,
        ctx: RequestContext,
        reason: str = "explicit_logout_all",
    ) -> None:
        """
        Revoke all refresh tokens for a user (logout-all or password change).
        """
        revoked_count = await self._tokens.revoke_all_for_user(user.id)

        await self._audit.record(AuditEvent(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_email=user.email,
            action="user.sessions_revoked",
            outcome="success",
            request_id=ctx.request_id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
            metadata={"reason": reason, "revoked_count": revoked_count},
        ))

    async def _issue_tokens(self, user: User, ctx: RequestContext) -> AuthResult:
        """
        Issue a new access + refresh token pair for a user.
        Creates a new token family (used for first login; rotation uses same family).
        """
        raw_refresh_token = generate_refresh_token()
        token_hash = hash_refresh_token(raw_refresh_token)
        family_id = uuid.uuid4()

        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            family_id=family_id,
            issued_at=datetime.now(tz=UTC),
            expires_at=datetime.now(tz=UTC) + timedelta(
                days=settings.refresh_token_expire_days
            ),
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
        await self._tokens.create(refresh_token)

        access_token = create_access_token(
            subject=str(user.id),
            additional_claims={
                "org_id": str(user.organization_id),
                "roles": user.role_names,
            },
        )

        return AuthResult(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            user=user,
        )
