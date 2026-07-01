"""Standardised cleaning framework (Task 7 + Task 12).

Pure-Python, side-effect-free cleaning primitives shared by every Silver
transform and re-used (as Spark UDF logic) by the Spark jobs. Cleaning happens
at the **Bronze -> Silver boundary**: Bronze stays immutable/raw; Silver is the
first place data is guaranteed conformed.

Design choices:
- *Correct vs reject*: recoverable issues (units, casing, parseable timestamps)
  are corrected; structural issues (missing keys, unparseable time, out-of-range
  geo) cause the record to be rejected to the quarantine dataset.
- Every rejection carries a machine-readable ``reason`` for audit + reconciliation.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable


@dataclass
class CleanResult:
    """Outcome of cleaning a single record."""

    record: dict[str, Any] | None
    rejected: bool = False
    reasons: list[str] = field(default_factory=list)

    @classmethod
    def keep(cls, record: dict[str, Any]) -> "CleanResult":
        return cls(record=record, rejected=False)

    @classmethod
    def reject(cls, reasons: list[str]) -> "CleanResult":
        return cls(record=None, rejected=True, reasons=reasons)


# --- Scalar coercion / normalization ---------------------------------------

def to_float(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_timestamp(value: Any) -> str | None:
    """Parse a timestamp and re-emit it as a UTC ISO-8601 string.

    Returns ``None`` when the value is missing or not parseable (the caller
    decides whether that is a rejection).
    """
    if value in (None, ""):
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).isoformat()


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def in_range(value: Any, lo: float, hi: float) -> bool:
    v = to_float(value)
    return v is not None and lo <= v <= hi


# --- Null / duplicate / outlier primitives ---------------------------------

def require_fields(record: dict[str, Any], fields: Iterable[str]) -> list[str]:
    """Return rejection reasons for any missing/null required field."""
    reasons: list[str] = []
    for f in fields:
        if record.get(f) in (None, ""):
            reasons.append(f"null:{f}")
    return reasons


def natural_key(record: dict[str, Any], key_fields: Iterable[str]) -> tuple:
    return tuple(record.get(f) for f in key_fields)


def stable_key(*parts: Any) -> str:
    """Deterministic short surrogate key from the given parts.

    Used to synthesise natural keys (e.g. ``fire_key``) for sources that do not
    ship a stable identifier of their own. Same inputs always hash to the same
    16-hex-character key so re-processing Bronze is idempotent.
    """
    joined = "|".join("" if p is None else str(p) for p in parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:16]


def deduplicate(records: list[dict[str, Any]], key_fields: Iterable[str],
                order_field: str = "_event_ts") -> list[dict[str, Any]]:
    """Keep the latest record per natural key (Task 3 dedup logic).

    Latest is decided by ``order_field`` descending; ties keep the last seen.
    """
    key_fields = list(key_fields)
    best: dict[tuple, dict[str, Any]] = {}
    for rec in records:
        k = natural_key(rec, key_fields)
        cur = best.get(k)
        if cur is None or str(rec.get(order_field, "")) >= str(cur.get(order_field, "")):
            best[k] = rec
    return list(best.values())


def is_outlier_zscore(value: float, mean: float, std: float, threshold: float = 4.0) -> bool:
    """Flag a value as an outlier when |z| exceeds ``threshold`` (Task 7)."""
    if std <= 0:
        return False
    return abs((value - mean) / std) > threshold


def median(values: list[float]) -> float | None:
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0
