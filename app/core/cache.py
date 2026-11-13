import json
import time
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("app.cache")


class CacheManager:
    """Async Redis cache with automatic in-memory TTL fallback and hit/miss telemetry."""

    def __init__(self) -> None:
        self._redis: Redis | None = None
        self._redis_available: bool = False
        self._memory_store: dict[str, tuple[float, str]] = {}
        self._hits: int = 0
        self._misses: int = 0
        self._invalidations: int = 0

    async def connect(self) -> None:
        """Attempt connection to Redis; fall back to in-memory cache if offline."""
        try:
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
            logger.info("Connected to Redis cache at %s", settings.REDIS_URL)
        except Exception as exc:
            self._redis = None
            self._redis_available = False
            logger.info(
                "Redis unavailable (%s); using in-memory TTL cache fallback",
                exc,
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

    async def get_json(self, key: str) -> Any | None:
        if self._redis_available and self._redis is not None:
            try:
                raw = await self._redis.get(key)
                if raw is not None:
                    self._hits += 1
                    return json.loads(raw)
                self._misses += 1
                return None
            except Exception:
                self._redis_available = False

        self._cleanup_expired_memory()
        entry = self._memory_store.get(key)
        if entry is None:
            self._misses += 1
            return None
        self._hits += 1
        return json.loads(entry[1])

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        ttl = ttl_seconds or settings.CACHE_TTL_SECONDS
        serialized = json.dumps(value, default=str)
        if self._redis_available and self._redis is not None:
            try:
                await self._redis.set(key, serialized, ex=ttl)
                return
            except Exception:
                self._redis_available = False

        self._cleanup_expired_memory()
        self._memory_store[key] = (time.monotonic() + ttl, serialized)

    async def invalidate_prefix(self, prefix: str) -> int:
        """Invalidate all cache keys starting with the given prefix."""
        deleted_count = 0
        if self._redis_available and self._redis is not None:
            try:
                keys = [k async for k in self._redis.scan_iter(match=f"{prefix}*")]
                if keys:
                    deleted_count += int(await self._redis.delete(*keys))
            except Exception:
                self._redis_available = False

        matching_mem = [k for k in self._memory_store if k.startswith(prefix)]
        for key in matching_mem:
            self._memory_store.pop(key, None)
            deleted_count += 1
        self._invalidations += deleted_count
        return deleted_count

    def get_stats(self) -> dict[str, Any]:
        """Return cache hit/miss telemetry and active backend details."""
        self._cleanup_expired_memory()
        total_lookups = self._hits + self._misses
        hit_rate = round((self._hits / total_lookups) * 100, 2) if total_lookups else 0.0
        return {
            "backend": "redis" if self._redis_available else "memory_fallback",
            "ttl_seconds": settings.CACHE_TTL_SECONDS,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": hit_rate,
            "invalidations": self._invalidations,
            "memory_keys_count": len(self._memory_store),
        }


cache_manager = CacheManager()
