"""
infrastructure/repositories/token_repository.py

Repository for RefreshToken persistence and family revocation.

Responsibilities:
- Persist new refresh tokens (hashed, with family context).
- Look up a token by its SHA-256 hash.
- Revoke a single token (record revoked_at timestamp).
- Revoke all tokens in a family (theft detection response).
- Revoke all tokens for a user (logout-all / password change).

Security notes:
- Only token hashes are stored; raw tokens are never persisted.
- Family revocation is atomic within the caller's session transaction.
- Expired token cleanup is intentionally deferred to a scheduled job (Phase 7).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models.user import RefreshToken


class TokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, token: RefreshToken) -> RefreshToken:
        """Persist a new refresh token. Caller commits the session."""
        self._session.add(token)
        await self._session.flush()
        return token

    async def find_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Find a refresh token by its SHA-256 hash."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, token: RefreshToken, replaced_by_id: uuid.UUID | None = None) -> None:
        """
        Mark a single token as revoked.

        Args:
            token: The RefreshToken ORM object to revoke.
            replaced_by_id: ID of the successor token (rotation chain), if any.
        """
        token.revoked_at = datetime.now(tz=UTC)
        if replaced_by_id is not None:
            token.replaced_by = replaced_by_id
        await self._session.flush()

    async def revoke_family(self, family_id: uuid.UUID) -> int:
        """
        Revoke all tokens in a token family.

        Used when a previously-revoked token is presented (possible theft).
        Returns the number of tokens revoked.
        """
        now = datetime.now(tz=UTC)
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        result = await self._session.execute(stmt)
        return int(result.rowcount)

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        """
        Revoke all non-revoked refresh tokens for a user.
        Used on logout-all and password change.
        """
        now = datetime.now(tz=UTC)
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        result = await self._session.execute(stmt)
        return int(result.rowcount)


