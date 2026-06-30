"""Base class for API connectors.

A connector pulls from one external source, wraps each raw record in a Bronze
envelope, and returns them for landing. Connectors do not know about MinIO or
Kafka — orchestration code (DAGs / producers) wires them to a sink. This keeps
connectors unit-testable with a mocked :class:`HttpClient`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable

from ingestion.common.envelope import BronzeEnvelope, build_envelope, new_batch_id
from ingestion.common.http import HttpClient, RateLimiter
from ingestion.common.logging_setup import get_logger


class ApiConnector(ABC):
    #: Short dataset code stored in the Bronze ``_source`` column.
    source_code: str = "UNKNOWN"
    #: Default conservative rate limit (calls/second).
    rate_limit_per_s: int = 5

    def __init__(self, http: HttpClient | None = None) -> None:
        self.log = get_logger(f"connector.{self.source_code}")
        self.http = http or HttpClient(rate_limit=RateLimiter(self.rate_limit_per_s, 1.0))

    @abstractmethod
    def fetch_raw(self, **kwargs) -> tuple[list[dict[str, Any]], str]:
        """Return ``(records, fmt)`` pulled from the source."""

    def _event_ts(self, record: dict[str, Any]) -> str | None:  # noqa: D401
        """Override to extract a source event timestamp for ``_event_ts``."""
        return None

    def ingest(self, **kwargs) -> list[BronzeEnvelope]:
        """Pull, then wrap each record in a Bronze envelope with provenance."""
        batch_id = new_batch_id(self.source_code)
        records, fmt = self.fetch_raw(**kwargs)
        envelopes = [
            build_envelope(
                source=self.source_code,
                payload=rec,
                batch_id=batch_id,
                fmt=fmt,
                event_ts=self._event_ts(rec),
            )
            for rec in records
        ]
        self.log.info("ingested %d records (batch=%s)", len(envelopes), batch_id)
        return envelopes


def parse_csv(text: str) -> list[dict[str, str]]:
    """Parse CSV text into a list of dict rows (stdlib only)."""
    import csv
    import io

    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]
