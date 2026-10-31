from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Any


@dataclass(frozen=True)
class CacheValue:
    value: dict[str, Any]
    expires_at: float
    stale_until: float


class FeatureResponseCache:
    def __init__(self, *, ttl_seconds: float = 2.0, stale_seconds: float = 60.0):
        if ttl_seconds <= 0 or stale_seconds < ttl_seconds:
            raise ValueError("Cache TTL must be positive and stale_seconds >= ttl_seconds.")
        self._ttl_seconds = ttl_seconds
        self._stale_seconds = stale_seconds
        self._entries: dict[str, CacheValue] = {}
        self._lock = Lock()

    def get(self, key: str, *, allow_stale: bool = False) -> tuple[dict[str, Any] | None, bool]:
        now = monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None, False
            if now < entry.expires_at:
                return entry.value.copy(), False
            if allow_stale and now < entry.stale_until:
                return entry.value.copy(), True
            if now >= entry.stale_until:
                self._entries.pop(key, None)
            return None, False

    def put(self, key: str, value: dict[str, Any]) -> None:
        now = monotonic()
        with self._lock:
            self._entries[key] = CacheValue(
                value=value.copy(),
                expires_at=now + self._ttl_seconds,
                stale_until=now + self._stale_seconds,
            )


def cache_key(payload: dict[str, Any]) -> str:
    import hashlib
    import json

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
