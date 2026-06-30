"""Bronze envelope — the standard provenance wrapper for every raw record.

Mirrors the Phase 6 data-modeling contract (docs/data-modeling/02-bronze-layer.md):
every record landed in Bronze carries ingest metadata so Silver/Gold can be
fully and traceably rebuilt.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_batch_id(source: str) -> str:
    """A human-readable, sortable ingestion-run id."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{source}-{stamp}-{uuid.uuid4().hex[:8]}"


def _checksum(payload: Any) -> str:
    raw = payload if isinstance(payload, (bytes, bytearray)) else json.dumps(
        payload, sort_keys=True, default=str
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass
class BronzeEnvelope:
    """Standard Bronze record. ``payload`` holds the raw source record as-is."""

    _ingest_id: str
    _source: str
    _ingest_ts: str
    _batch_id: str
    _format: str
    _checksum: str
    payload: Any
    _event_ts: str | None = None
    _source_uri: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


def build_envelope(
    *,
    source: str,
    payload: Any,
    batch_id: str,
    fmt: str = "json",
    event_ts: str | None = None,
    source_uri: str | None = None,
) -> BronzeEnvelope:
    """Wrap a raw record in the Bronze envelope with full provenance."""
    return BronzeEnvelope(
        _ingest_id=str(uuid.uuid4()),
        _source=source,
        _ingest_ts=_utcnow_iso(),
        _event_ts=event_ts,
        _batch_id=batch_id,
        _format=fmt,
        _checksum=_checksum(payload),
        _source_uri=source_uri,
        payload=payload,
    )
