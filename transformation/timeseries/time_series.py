"""Time-series processing primitives (Task 11).

Window alignment, resampling, and gap handling used by the telemetry Silver/Gold
transforms and feature engineering. Dependency-free so it runs offline; the
Spark jobs apply the same semantics with windowed aggregations.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable


def parse_ts(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)


def floor_to_window(ts: datetime, window_s: int) -> datetime:
    """Align a timestamp to the start of its fixed window (e.g. minute/hour)."""
    epoch = int(ts.timestamp())
    floored = epoch - (epoch % window_s)
    return datetime.fromtimestamp(floored, tz=timezone.utc)


def window_key(value: Any, window_s: int) -> str | None:
    ts = parse_ts(value)
    if ts is None:
        return None
    return floor_to_window(ts, window_s).isoformat()


def resample_mean(points: list[dict[str, Any]], value_field: str, window_s: int,
                  ts_field: str = "timestamp") -> list[dict[str, Any]]:
    """Down-sample an irregular series to fixed windows using the window mean.

    Returns one row per occupied window: ``{window_start, count, mean}``.
    """
    buckets: dict[str, list[float]] = {}
    for p in points:
        wk = window_key(p.get(ts_field), window_s)
        v = p.get(value_field)
        if wk is None or v is None:
            continue
        try:
            buckets.setdefault(wk, []).append(float(v))
        except (TypeError, ValueError):
            continue
    out = []
    for wk in sorted(buckets):
        vals = buckets[wk]
        out.append({
            "window_start": wk,
            "count": len(vals),
            "mean": round(sum(vals) / len(vals), 6),
        })
    return out


def find_gaps(points: list[dict[str, Any]], expected_interval_s: float,
              ts_field: str = "timestamp", tolerance: float = 1.5) -> list[dict[str, Any]]:
    """Detect missing-timestamp gaps in an ordered series (Task 11).

    A gap is any inter-arrival interval longer than ``expected_interval_s *
    tolerance``. Returns the gap boundaries and estimated number of missing
    samples — input to interpolation/anomaly preprocessing.
    """
    ordered = sorted(
        (p for p in points if parse_ts(p.get(ts_field))),
        key=lambda p: parse_ts(p[ts_field]),  # type: ignore[arg-type]
    )
    gaps = []
    for prev, cur in zip(ordered, ordered[1:]):
        t0 = parse_ts(prev[ts_field])
        t1 = parse_ts(cur[ts_field])
        delta = (t1 - t0).total_seconds()  # type: ignore[union-attr]
        if delta > expected_interval_s * tolerance:
            gaps.append({
                "gap_start": t0.isoformat(),  # type: ignore[union-attr]
                "gap_end": t1.isoformat(),  # type: ignore[union-attr]
                "gap_seconds": round(delta, 3),
                "missing_estimate": int(delta / expected_interval_s) - 1,
            })
    return gaps


def interpolate_linear(t0: float, v0: float, t1: float, v1: float, t: float) -> float:
    """Linear interpolation of a value at time ``t`` between two samples."""
    if t1 == t0:
        return v0
    ratio = (t - t0) / (t1 - t0)
    return v0 + (v1 - v0) * ratio


def rolling_mean(values: Iterable[float], window: int) -> list[float]:
    """Trailing rolling mean; output aligns to the right edge of the window."""
    vals = list(values)
    out: list[float] = []
    acc: list[float] = []
    for v in vals:
        acc.append(v)
        if len(acc) > window:
            acc.pop(0)
        out.append(round(sum(acc) / len(acc), 6))
    return out
