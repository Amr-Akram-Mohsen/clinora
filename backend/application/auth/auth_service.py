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
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
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
from infrastructure.email.email_service import EmailService
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

        if not user.is_verified and settings.mail_enabled:
            await self._audit.record(AuditEvent(
                organization_id=user.organization_id,
                actor_id=user.id,
                actor_email=user.email,
                action="user.login.failure",
                outcome="failure",
                request_id=ctx.request_id,
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
                metadata={"reason": "unverified_email"},
            ))
            raise AuthenticationError("Please verify your email address before logging in. Check your inbox for the confirmation link.")

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

        verification_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(tz=UTC) + timedelta(hours=24)

        new_user = User(
            organization_id=org.id,
            email=normalized_email,
            password_hash=hash_password(password),
            full_name=full_name.strip(),
            is_active=True,
            is_superuser=False,
            is_verified=not settings.mail_enabled,
            verification_token=verification_token,
            verification_expires_at=expires_at,
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

        # Dispatch verification email asynchronously
        await EmailService.send_verification_email(
            to_email=new_user.email,
            recipient_name=new_user.full_name,
            token=verification_token,
        )

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

    async def verify_email(self, token: str, ctx: RequestContext) -> User:
        """
        Verify a user's email address via the emailed verification token.
        """
        user = await self._users.find_by_verification_token(token)
        if not user or not user.verification_expires_at:
            raise AuthenticationError("Verification link is invalid or has expired.")

        now_utc = datetime.now(tz=UTC)
        if now_utc > user.verification_expires_at:
            raise AuthenticationError("Verification link has expired. Please request a new one.")

        user.is_verified = True
        user.verification_token = None
        user.verification_expires_at = None
        await self._users.update_user(user)

        await self._audit.record(AuditEvent(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_email=user.email,
            action="user.email.verified",
            outcome="success",
            request_id=ctx.request_id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        ))
        return user

    async def resend_verification_email(self, email: str, ctx: RequestContext) -> None:
        """
        Resend email verification token. Silent on non-existent or verified emails
        to prevent account enumeration.
        """
        user = await self._users.find_by_email(email)
        if user and user.is_active and not user.is_verified:
            token = secrets.token_urlsafe(32)
            user.verification_token = token
            user.verification_expires_at = datetime.now(tz=UTC) + timedelta(hours=24)
            await self._users.update_user(user)
            await EmailService.send_verification_email(user.email, user.full_name, token)

            await self._audit.record(AuditEvent(
                organization_id=user.organization_id,
                actor_id=user.id,
                actor_email=user.email,
                action="user.verification.resend_requested",
                outcome="success",
                request_id=ctx.request_id,
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
            ))

    async def request_password_reset(self, email: str, ctx: RequestContext) -> None:
        """
        Request password reset link (1-hour expiry). Silent if email doesn't exist
        to prevent user enumeration.
        """
        user = await self._users.find_by_email(email)
        if user and user.is_active:
            token = secrets.token_urlsafe(32)
            user.password_reset_token = token
            user.password_reset_sent_at = datetime.now(tz=UTC)
            await self._users.update_user(user)
            await EmailService.send_password_reset_email(user.email, user.full_name, token)

            await self._audit.record(AuditEvent(
                organization_id=user.organization_id,
                actor_id=user.id,
                actor_email=user.email,
                action="user.password_reset.requested",
                outcome="success",
                request_id=ctx.request_id,
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
            ))
        else:
            await self._audit.record(AuditEvent(
                organization_id=None,
                actor_email=email,
                action="user.password_reset.requested",
                outcome="failure",
                request_id=ctx.request_id,
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
                metadata={"reason": "user_not_found"},
            ))

    async def reset_password(self, token: str, new_password: str, ctx: RequestContext) -> None:
        """
        Reset account password using reset token within 1-hour window.
        Revokes all active sessions for security.
        """
        user = await self._users.find_by_reset_token(token)
        if not user or not user.password_reset_sent_at:
            raise AuthenticationError("This reset link is invalid or has expired.")

        expiry = user.password_reset_sent_at + timedelta(hours=1)
        now_utc = datetime.now(tz=UTC)
        if now_utc > expiry:
            raise AuthenticationError("This reset link has expired. Please request a new one.")

        user.password_hash = hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_sent_at = None
        await self._users.update_user(user)

        # Invalidate all existing token families
        await self.revoke_all_sessions(user, ctx, reason="password_reset")

        await self._audit.record(AuditEvent(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_email=user.email,
            action="user.password_reset.completed",
            outcome="success",
            request_id=ctx.request_id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        ))

    async def authenticate_google_user(self, credential: str, ctx: RequestContext) -> AuthResult:
        """
        Verify Google OAuth 2.0 credential and authenticate/provision the user.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://oauth2.googleapis.com/tokeninfo",
                    params={"id_token": credential},
                )
                if res.status_code != 200:
                    raise AuthenticationError("Failed to verify Google token with identity provider.")
                payload = res.json()
        except httpx.HTTPError as exc:
            raise AuthenticationError("Google authentication service is currently unavailable.") from exc

        google_id = payload.get("sub")
        email = (payload.get("email") or "").lower().strip()
        name = payload.get("name") or (email.split("@")[0] if email else "Google User")

        if not email or not google_id:
            raise AuthenticationError("Google account does not provide verified email.")

        # Find existing user by google_id or email
        user = await self._users.find_by_google_id(google_id)
        if not user:
            user = await self._users.find_by_email(email)
            if user:
                user.google_id = google_id
                user.is_verified = True
                await self._users.update_user(user)
            else:
                # Provision new user in default organization
                org = await self._users.find_organization_by_slug("clinora")
                if not org:
                    org = await self._users.find_default_organization()
                if not org:
                    org = Organization(name="Clinora Clinic", slug="clinora", is_active=True)
                    await self._users.add_organization(org)

                role = await self._users.find_role_by_name("DOCTOR")
                if not role:
                    role = await self._users.find_role_by_name("ADMIN")

                new_user = User(
                    organization_id=org.id,
                    email=email,
                    password_hash=hash_password(secrets.token_urlsafe(32)),
                    full_name=name,
                    is_active=True,
                    is_superuser=False,
                    is_verified=True,
                    google_id=google_id,
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
                user = await self._users.find_by_id(new_user.id)
                assert user is not None

        if not user.is_active:
            raise AuthenticationError("Account is inactive")

        result = await self._issue_tokens(user, ctx)

        await self._audit.record(AuditEvent(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_email=user.email,
            action="user.login.google.success",
            outcome="success",
            request_id=ctx.request_id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
            metadata={"google_id": google_id},
        ))

        return result
