import asyncio
import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.cache import cache_manager
from app.core.config import settings
from app.core.constants import PASSWORD_MAX_LENGTH
from app.core.exceptions import BadRequestException, UnauthorizedException


def _encode_password_bytes(plain_password: str) -> bytes:
    encoded = plain_password.encode("utf-8")
    if len(encoded) > PASSWORD_MAX_LENGTH:
        raise BadRequestException(
            f"Password must not exceed {PASSWORD_MAX_LENGTH} UTF-8 bytes"
        )
    return encoded


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt synchronously."""
    password_bytes = _encode_password_bytes(plain_password)
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


async def hash_password_async(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt in a background thread."""
    return await asyncio.to_thread(hash_password, plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against bcrypt or legacy sha256 hashes."""
    if hashed_password.startswith("sha256$"):
        expected = (
            f"sha256${hashlib.sha256(plain_password.encode('utf-8')).hexdigest()}"
        )
        return expected == hashed_password
    try:
        password_bytes = _encode_password_bytes(plain_password)
        return bcrypt.checkpw(
            password_bytes,
            hashed_password.encode("utf-8"),
        )
    except (ValueError, BadRequestException):
        return False


async def verify_password_async(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password using bcrypt in a background thread."""
    return await asyncio.to_thread(verify_password, plain_password, hashed_password)


def create_access_token(
    subject: int | str,
    *,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Generate a signed JWT access token."""
    now = datetime.now(UTC)
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
    now = datetime.now(UTC)
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
    now_ts = int(datetime.now(UTC).timestamp())
    ttl = max(exp_timestamp - now_ts, 60)
    await cache_manager.set_json(f"revoked_jti:{jti}", {"revoked": True}, ttl_seconds=ttl)


async def consume_token_atomically(jti: str, exp_timestamp: int) -> bool:
    """Atomically mark a refresh token JTI as consumed; returns False if already used/revoked."""
    now_ts = int(datetime.now(UTC).timestamp())
    ttl = max(exp_timestamp - now_ts, 60)
    return await cache_manager.set_if_absent(
        f"revoked_jti:{jti}",
        {"revoked": True},
        ttl_seconds=ttl,
    )


async def is_token_revoked(jti: str) -> bool:
    """Check whether a token JTI has been revoked (without polluting task cache metrics)."""
    data = await cache_manager.get_json(f"revoked_jti:{jti}", namespace=None)
    return data is not None


async def increment_user_token_version(user_id: int) -> int:
    """Increment user token generation counter to invalidate tokens issued before password change."""
    key = f"user_tok_ver:{user_id}"
    current = await cache_manager.get_json(key, namespace=None)
    next_ver = int(current["ver"]) + 1 if isinstance(current, dict) and "ver" in current else 2
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    await cache_manager.set_json(
        key,
        {"ver": next_ver, "revoked_at": int(datetime.now(UTC).timestamp())},
        ttl_seconds=ttl,
    )
    return next_ver


async def get_user_password_changed_at(user_id: int) -> int | None:
    """Return unix timestamp of most recent password change for user, if any."""
    data = await cache_manager.get_json(f"user_tok_ver:{user_id}", namespace=None)
    if isinstance(data, dict) and "revoked_at" in data:
        return int(data["revoked_at"])
    return None
