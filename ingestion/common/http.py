"""Resilient HTTP client for API ingestion.

Implements the Task 4 cross-cutting concerns: retry with exponential backoff,
rate limiting, timeouts, and a shared session. Connectors build on this instead
of calling ``requests`` directly.
"""

from __future__ import annotations

import time
from collections import deque
from threading import Lock

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ingestion.common.logging_setup import get_logger

log = get_logger(__name__)

DEFAULT_TIMEOUT = 30


class RateLimiter:
    """Simple token-free sliding-window limiter: ``max_calls`` per ``period`` s."""

    def __init__(self, max_calls: int, period: float = 1.0) -> None:
        self.max_calls = max_calls
        self.period = period
        self._calls: deque[float] = deque()
        self._lock = Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            while self._calls and now - self._calls[0] > self.period:
                self._calls.popleft()
            if len(self._calls) >= self.max_calls:
                sleep_for = self.period - (now - self._calls[0])
                if sleep_for > 0:
                    log.debug("rate limit hit; sleeping %.2fs", sleep_for)
                    time.sleep(sleep_for)
            self._calls.append(time.monotonic())


class HttpClient:
    """A reusable session with retry/backoff and an optional rate limiter."""

    def __init__(
        self,
        *,
        rate_limit: RateLimiter | None = None,
        total_retries: int = 4,
        backoff_factor: float = 0.8,
        user_agent: str = "space-platform-ingestion/0.1",
    ) -> None:
        self.rate_limit = rate_limit
        self.session = requests.Session()
        retry = Retry(
            total=total_retries,
            backoff_factor=backoff_factor,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST"),
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_maxsize=10)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update({"User-Agent": user_agent})

    def get(self, url: str, *, params: dict | None = None, headers: dict | None = None,
            timeout: int = DEFAULT_TIMEOUT) -> requests.Response:
        if self.rate_limit:
            self.rate_limit.acquire()
        log.debug("GET %s params=%s", url, params)
        return self.session.get(url, params=params, headers=headers, timeout=timeout)

    def get_json(self, url: str, **kwargs):
        resp = self.get(url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def post(self, url: str, *, data: dict | None = None, json: dict | None = None,
             headers: dict | None = None, timeout: int = DEFAULT_TIMEOUT) -> requests.Response:
        if self.rate_limit:
            self.rate_limit.acquire()
        log.debug("POST %s", url)
        return self.session.post(url, data=data, json=json, headers=headers, timeout=timeout)

    def post_json(self, url: str, **kwargs):
        resp = self.post(url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self.session.close()
