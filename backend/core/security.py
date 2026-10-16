"""
core/security.py

Authentication primitives: JWT encoding/decoding and password hashing.

Responsibilities:
- Create and validate access tokens (short-lived JWTs).
- Hash and verify passwords using bcrypt.
- Generate cryptographically secure random tokens (for refresh tokens).

Non-goals:
- Does not manage refresh token lifecycle (created/rotated/revoked in
  infrastructure/repositories/token_repository.py via AuthService).
- Does not touch FastAPI request state or HTTP concerns.

Security notes:
- Access tokens expire in ACCESS_TOKEN_EXPIRE_MINUTES (default 15 min).
- Refresh tokens are stored as SHA-256 hashes in the DB, never raw.
- The SECRET_KEY must be at least 32 characters (validated in config).
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

_ALGORITHM = "HS256"
_TOKEN_TYPE_ACCESS = "access"

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the plaintext password."""
    return cast(str, _pwd_context.hash(plain))


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if `plain` matches the stored bcrypt `hashed` value."""
    return cast(bool, _pwd_context.verify(plain, hashed))


# ---------------------------------------------------------------------------
# Access tokens (JWT)
# ---------------------------------------------------------------------------


def create_access_token(
    subject: str,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: Typically the user's UUID string.
        additional_claims: Extra claims to embed (e.g., roles, org_id).

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(tz=UTC)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": _TOKEN_TYPE_ACCESS,
    }
    if additional_claims:
        payload.update(additional_claims)

    return cast(str, jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM))


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Raises:
        core.errors.AuthenticationError: If the token is invalid or expired.

    Returns:
        The decoded payload dict.
    """
    from core.errors import AuthenticationError

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
    except JWTError as err:
        raise AuthenticationError("Invalid or expired access token") from err

    if payload.get("type") != _TOKEN_TYPE_ACCESS:
        raise AuthenticationError("Invalid token type")

    return cast(dict[str, Any], payload)



# ---------------------------------------------------------------------------
# Refresh tokens
# ---------------------------------------------------------------------------


def generate_refresh_token() -> str:
    """
    Generate a cryptographically secure random refresh token (URL-safe, 64 bytes).
    The raw token is given to the client; only its hash is stored in the DB.
    """
    return secrets.token_urlsafe(64)


def hash_refresh_token(raw_token: str) -> str:
    """Return the SHA-256 hex digest of a raw refresh token for DB storage."""
    return hashlib.sha256(raw_token.encode()).hexdigest()
