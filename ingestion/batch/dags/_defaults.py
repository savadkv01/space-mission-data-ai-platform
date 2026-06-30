"""Shared defaults for ingestion DAGs (retry/backoff strategy — Task 3)."""

from __future__ import annotations

from datetime import timedelta

# Standard retry + exponential backoff for all ingestion tasks.
DEFAULT_ARGS = {
    "owner": "data-eng",
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
    "depends_on_past": False,
}
