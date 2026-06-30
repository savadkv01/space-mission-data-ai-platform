"""Validation rules applied at ingestion (Task 9).

Validation happens *after* a record is durably landed in Bronze (so nothing is
ever lost) and *before* it is promoted to the cleaned stream. Records that fail
are routed to quarantine / DLQ rather than dropped.

Rule families:
- schema validation (required fields, types, ranges) via the schema registry
- null checks, range validation
- duplicate detection (checksum-based, in-window)
- timestamp validation (parseable, not absurdly future/past)
- geospatial validation (lat/lon bounds)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from ingestion.common.schemas import Schema, get_schema


@dataclass
class ValidationOutcome:
    valid: bool
    errors: list[str] = field(default_factory=list)
    rule_hits: list[str] = field(default_factory=list)

    @classmethod
    def ok(cls) -> "ValidationOutcome":
        return cls(valid=True)


def _check_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return "timestamp: not ISO-8601 parseable"
    now = datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    if ts > now + timedelta(days=2):
        return "timestamp: too far in the future"
    if ts < now - timedelta(days=3650):
        return "timestamp: implausibly old"
    return None


def _check_geo(record: dict[str, Any]) -> list[str]:
    errors = []
    lat, lon = record.get("latitude"), record.get("longitude")
    if lat is not None and not (-90 <= _as_float(lat, 999) <= 90):
        errors.append("geo: latitude out of range")
    if lon is not None and not (-180 <= _as_float(lon, 999) <= 180):
        errors.append("geo: longitude out of range")
    return errors


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class DuplicateTracker:
    """In-memory, bounded checksum set for near-duplicate detection per stream."""

    def __init__(self, capacity: int = 100_000) -> None:
        self.capacity = capacity
        self._seen: set[str] = set()
        self._order: list[str] = []

    def is_duplicate(self, checksum: str) -> bool:
        if checksum in self._seen:
            return True
        self._seen.add(checksum)
        self._order.append(checksum)
        if len(self._order) > self.capacity:
            oldest = self._order.pop(0)
            self._seen.discard(oldest)
        return False


def validate_record(record: dict[str, Any], *, schema: str | Schema | None = None,
                    checksum: str | None = None, dedup: DuplicateTracker | None = None
                    ) -> ValidationOutcome:
    """Validate one decoded record. ``record`` is the source payload (not the
    full Bronze envelope)."""
    errors: list[str] = []
    rule_hits: list[str] = []

    schema_obj = get_schema(schema) if isinstance(schema, str) else schema
    if schema_obj is not None:
        schema_errors = schema_obj.validate(record)
        if schema_errors:
            errors.extend(schema_errors)
            rule_hits.append("schema")

    ts_error = _check_timestamp(record.get("timestamp") or record.get("acq_date"))
    if ts_error:
        errors.append(ts_error)
        rule_hits.append("timestamp")

    geo_errors = _check_geo(record)
    if geo_errors:
        errors.extend(geo_errors)
        rule_hits.append("geospatial")

    if dedup is not None and checksum is not None and dedup.is_duplicate(checksum):
        errors.append("duplicate: checksum already seen in window")
        rule_hits.append("duplicate")

    return ValidationOutcome(valid=not errors, errors=errors, rule_hits=rule_hits)
