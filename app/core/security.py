from datetime import datetime, timedelta, timezone
import hashlib
from typing import Any
import uuid

import bcrypt
import jwt

from app.core.cache import cache_manager
from app.core.config import settings
from app.core.exceptions import UnauthorizedException


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    password_bytes = plain_password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against bcrypt or legacy sha256 hashes."""
    if hashed_password.startswith("sha256$"):
        expected = (
            f"sha256${hashlib.sha256(plain_password.encode('utf-8')).hexdigest()}"
        )
        return expected == hashed_password
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def create_access_token(
    subject: int | str,
    *,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Generate a signed JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: int | str,
    *,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Generate a signed JWT refresh token."""
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_jwt_token(token: str, *, expected_type: str | None = None) -> dict[str, Any]:
    """Decode and validate a JWT token, raising UnauthorizedException on failure."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedException("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedException("Invalid authentication token") from exc

    token_type = payload.get("type")
    if expected_type is not None and token_type != expected_type:
        raise UnauthorizedException(f"Expected '{expected_type}' token, got '{token_type}'")
    return payload


async def revoke_token(jti: str, exp_timestamp: int) -> None:
    """Store revoked token JTI in Redis/memory blacklist until its expiration."""
    now_ts = int(datetime.now(timezone.utc).timestamp())
    ttl = max(exp_timestamp - now_ts, 60)
    await cache_manager.set_json(f"revoked_jti:{jti}", {"revoked": True}, ttl_seconds=ttl)


async def is_token_revoked(jti: str) -> bool:
    """Check whether a token JTI has been revoked."""
    data = await cache_manager.get_json(f"revoked_jti:{jti}")
    return data is not None

