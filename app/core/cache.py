import json
import re
import time
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.constants import MEMORY_CACHE_MAX_KEYS
from app.core.logging import get_logger

logger = get_logger("app.cache")


def mask_redis_url(url: str) -> str:
    """Mask password credentials in a Redis connection URL before logging."""
    return re.sub(r"(redis(?:s)?://[^:]*:)[^@]+(@)", r"\1***\2", url)


class CacheManager:
    """Async Redis cache with automatic retry, bounded memory fallback, and per-namespace stats."""

    def __init__(self) -> None:
        self._redis: Redis | None = None
        self._redis_available: bool = False
        self._next_retry_at: float = 0.0
        self._memory_store: dict[str, tuple[float, str]] = {}
        self._namespace_stats: dict[str, dict[str, int]] = {}

    async def connect(self) -> None:
        """Attempt connection to Redis; schedule retry on failure."""
        masked_url = mask_redis_url(settings.REDIS_URL)
        try:
            if self._redis is not None:
                await self._redis.aclose()
            client: Redis = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=1.5,
                socket_timeout=1.5,
            )
            await client.ping()
            self._redis = client
            self._redis_available = True
            self._next_retry_at = 0.0
            logger.info("Connected to Redis cache at %s", masked_url)
        except (RedisError, OSError) as exc:
            self._redis = None
            self._redis_available = False
            self._next_retry_at = (
                time.monotonic() + settings.REDIS_RETRY_COOLDOWN_SECONDS
            )
            logger.warning(
                "Redis unavailable at %s (%s); using bounded memory fallback (retry in %.1fs)",
                masked_url,
                exc,
                settings.REDIS_RETRY_COOLDOWN_SECONDS,
            )

    async def _ensure_redis(self) -> bool:
        """Return True if Redis is active, attempting reconnection after cooldown if previously down."""
        if self._redis_available and self._redis is not None:
            return True
        if time.monotonic() >= self._next_retry_at:
            await self.connect()
        return self._redis_available and self._redis is not None

    def _handle_redis_error(self, exc: Exception) -> None:
        self._redis_available = False
        self._next_retry_at = (
            time.monotonic() + settings.REDIS_RETRY_COOLDOWN_SECONDS
        )
        logger.warning(
            "Redis command failed (%s); falling back to memory and retrying in %.1fs",
            exc,
            settings.REDIS_RETRY_COOLDOWN_SECONDS,
        )

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
            self._redis_available = False

    def _cleanup_expired_memory(self) -> None:
        now = time.monotonic()
        expired = [k for k, (exp, _) in self._memory_store.items() if exp <= now]
        for key in expired:
            self._memory_store.pop(key, None)
        while len(self._memory_store) >= MEMORY_CACHE_MAX_KEYS:
            oldest_key = next(iter(self._memory_store))
            self._memory_store.pop(oldest_key, None)

    async def _record_metric(
        self,
        namespace: str | None,
        metric: str,
        delta: int = 1,
    ) -> None:
        if not namespace or delta <= 0:
            return
        bucket = self._namespace_stats.setdefault(
            namespace,
            {"hits": 0, "misses": 0, "invalidations": 0},
        )
        bucket[metric] = bucket.get(metric, 0) + delta

        if self._redis_available and self._redis is not None:
            try:
                await self._redis.incrby(f"stats:{namespace}:{metric}", delta)
            except (RedisError, OSError) as exc:
                self._handle_redis_error(exc)

    async def get_json(
        self,
        key: str,
        *,
        namespace: str | None = None,
    ) -> Any | None:
        if await self._ensure_redis() and self._redis is not None:
            try:
                raw = await self._redis.get(key)
                if raw is not None:
                    await self._record_metric(namespace, "hits")
                    return json.loads(raw)
                await self._record_metric(namespace, "misses")
                return None
            except (RedisError, OSError) as exc:
                self._handle_redis_error(exc)

        self._cleanup_expired_memory()
        entry = self._memory_store.get(key)
        if entry is None:
            await self._record_metric(namespace, "misses")
            return None
        await self._record_metric(namespace, "hits")
        return json.loads(entry[1])

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        ttl = ttl_seconds or settings.CACHE_TTL_SECONDS
        serialized = json.dumps(value, default=str)
        if await self._ensure_redis() and self._redis is not None:
            try:
                await self._redis.set(key, serialized, ex=ttl)
                return
            except (RedisError, OSError) as exc:
                self._handle_redis_error(exc)

        self._cleanup_expired_memory()
        self._memory_store[key] = (time.monotonic() + ttl, serialized)

    async def set_if_absent(
        self,
        key: str,
        value: Any,
        ttl_seconds: int,
    ) -> bool:
        """Atomically store key only if it does not already exist (returns True if newly set)."""
        serialized = json.dumps(value, default=str)
        if await self._ensure_redis() and self._redis is not None:
            try:
                result = await self._redis.set(key, serialized, ex=ttl_seconds, nx=True)
                return bool(result)
            except (RedisError, OSError) as exc:
                self._handle_redis_error(exc)

        self._cleanup_expired_memory()
        if key in self._memory_store:
            return False
        self._memory_store[key] = (time.monotonic() + ttl_seconds, serialized)
        return True

    async def invalidate_prefix(
        self,
        prefix: str,
        *,
        namespace: str | None = None,
    ) -> int:
        """Invalidate all cache keys starting with the given prefix."""
        deleted_count = 0
        if await self._ensure_redis() and self._redis is not None:
            try:
                keys = [k async for k in self._redis.scan_iter(match=f"{prefix}*")]
                if keys:
                    deleted_count += int(await self._redis.delete(*keys))
            except (RedisError, OSError) as exc:
                self._handle_redis_error(exc)

        matching_mem = [k for k in self._memory_store if k.startswith(prefix)]
        for key in matching_mem:
            self._memory_store.pop(key, None)
            deleted_count += 1

        if deleted_count > 0:
            await self._record_metric(namespace, "invalidations", deleted_count)
        return deleted_count

    async def get_namespace_stats(self, namespace: str) -> dict[str, Any]:
        """Return cache hit/miss telemetry for a specific namespace (from Redis INCR counters or memory fallback)."""
        hits = 0
        misses = 0
        invalidations = 0
        if await self._ensure_redis() and self._redis is not None:
            try:
                raw_vals = await self._redis.mget(
                    f"stats:{namespace}:hits",
                    f"stats:{namespace}:misses",
                    f"stats:{namespace}:invalidations",
                )
                hits = int(raw_vals[0] or 0)
                misses = int(raw_vals[1] or 0)
                invalidations = int(raw_vals[2] or 0)
            except (RedisError, OSError) as exc:
                self._handle_redis_error(exc)

        if not self._redis_available:
            bucket = self._namespace_stats.get(namespace, {})
            hits = bucket.get("hits", 0)
            misses = bucket.get("misses", 0)
            invalidations = bucket.get("invalidations", 0)

        total_lookups = hits + misses
        hit_rate = round((hits / total_lookups) * 100, 2) if total_lookups else 0.0
        return {
            "namespace": namespace,
            "backend": "redis" if self._redis_available else "memory_fallback",
            "ttl_seconds": settings.CACHE_TTL_SECONDS,
            "hits": hits,
            "misses": misses,
            "hit_rate_percent": hit_rate,
            "invalidations": invalidations,
        }


cache_manager = CacheManager()
