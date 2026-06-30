"""Shared utilities for the data source pre-flight checks.

Keeps every check small and consistent: a single HTTP session with sane
timeouts/retries, a standard result object, and a helper to persist a small
ingestion sample to ``output/`` for visual confirmation.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Status codes ----------------------------------------------------------
PASS = "PASS"   # reachable and (if creds given) authenticated
FAIL = "FAIL"   # reachable but rejected (bad/missing required creds) or error
SKIP = "SKIP"   # optional creds not supplied; check not attempted
WARN = "WARN"   # reachable but response was unexpected / partial

TOOL_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = TOOL_DIR / "output"
DEFAULT_TIMEOUT = 30  # seconds


@dataclass
class CheckResult:
    """Outcome of a single data source verification."""

    name: str
    category: str
    prerequisite: str
    status: str = SKIP
    message: str = ""
    sample_path: Path | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def line(self) -> str:
        sample = f"  -> sample: {self.sample_path.name}" if self.sample_path else ""
        return f"[{self.status:<4}] {self.name:<26} | {self.message}{sample}"


def load_environment() -> None:
    """Load credentials from the tool's local .env (if present)."""
    load_dotenv(TOOL_DIR / ".env")


def env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is not None:
        value = value.strip()
    return value or default


def build_session() -> requests.Session:
    """A requests session with retry/backoff for transient network errors."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "space-platform-preflight/1.0"})
    return session


def save_sample(filename: str, content: bytes | str) -> Path:
    """Persist a small ingestion sample under output/ and return its path."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    mode = "wb" if isinstance(content, bytes) else "w"
    encoding = None if isinstance(content, bytes) else "utf-8"
    with open(path, mode, encoding=encoding) as handle:
        handle.write(content)
    return path


def save_json_sample(filename: str, data: Any) -> Path:
    return save_sample(filename, json.dumps(data, indent=2, default=str))


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
