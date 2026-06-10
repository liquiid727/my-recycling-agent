"""CN: 缓存抽象层，统一内存缓存与 Redis 缓存的 TTL 读写接口。
EN: Cache abstraction that normalizes TTL reads and writes across in-memory and Redis backends.
"""

from __future__ import annotations

import json
import time
from hashlib import sha1
from typing import Any


class CacheBackend:
    def get_json(self, key: str) -> Any | None:
        raise NotImplementedError

    def set_json(self, key: str, value: Any, *, ttl_seconds: int) -> None:
        raise NotImplementedError

    def clear_prefix(self, prefix: str) -> None:
        raise NotImplementedError


class InMemoryCacheBackend(CacheBackend):
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, str]] = {}

    def get_json(self, key: str) -> Any | None:
        record = self._store.get(key)
        if record is None:
            return None
        expires_at, payload = record
        if expires_at < time.time():
            self._store.pop(key, None)
            return None
        return json.loads(payload)

    def set_json(self, key: str, value: Any, *, ttl_seconds: int) -> None:
        self._store[key] = (time.time() + ttl_seconds, json.dumps(value, ensure_ascii=False))

    def clear_prefix(self, prefix: str) -> None:
        for key in [key for key in self._store if key.startswith(prefix)]:
            self._store.pop(key, None)


class RedisCacheBackend(CacheBackend):
    def __init__(self, client: Any) -> None:
        self._client = client

    def get_json(self, key: str) -> Any | None:
        payload = self._client.get(key)
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return json.loads(payload)

    def set_json(self, key: str, value: Any, *, ttl_seconds: int) -> None:
        self._client.setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False))

    def clear_prefix(self, prefix: str) -> None:
        for key in self._client.scan_iter(f"{prefix}*"):
            self._client.delete(key)


def build_cache_backend(redis_url: str | None) -> CacheBackend:
    if not redis_url:
        return InMemoryCacheBackend()
    try:
        from redis import Redis
    except ImportError:
        return InMemoryCacheBackend()
    return RedisCacheBackend(Redis.from_url(redis_url, decode_responses=True))


def weather_cache_key(*, city_code: str, region_code: str, forecast_date: str) -> str:
    return f"weather:{city_code}:{region_code}:{forecast_date}"


def ride_plan_cache_key(request_payload: dict[str, Any]) -> str:
    payload = json.dumps(request_payload, ensure_ascii=False, sort_keys=True)
    digest = sha1(payload.encode("utf-8")).hexdigest()[:16]
    return f"ride-plan:{digest}"
