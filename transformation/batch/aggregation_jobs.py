"""Reusable aggregation jobs (Task 9).

Generic time/entity/geo aggregation helpers used to build Gold marts and
pre-aggregated rollups. Kept separate from the domain-specific Gold transforms
so aggregation granularity is configurable in one place.

Granularity catalogue:
- time: minute (60), hour (3600), day (86400)
- entity: satellite, mission
- geo: 0.25-degree grid cell
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Iterable

from transformation.timeseries.time_series import window_key

WINDOWS = {"minute": 60, "hour": 3600, "day": 86400}


def aggregate_time(records: list[dict[str, Any]], value_field: str, grain: str,
                   key_fields: Iterable[str] = (), ts_field: str = "event_ts",
                   agg: str = "mean") -> list[dict[str, Any]]:
    """Aggregate a value field into fixed time windows, optionally per entity.

    ``agg`` is one of ``mean|sum|min|max|count``.
    """
    if grain not in WINDOWS:
        raise ValueError(f"unknown grain: {grain}")
    window_s = WINDOWS[grain]
    key_fields = list(key_fields)
    buckets: dict[tuple, list[float]] = defaultdict(list)
    for r in records:
        wk = window_key(r.get(ts_field), window_s)
        if wk is None:
            continue
        v = r.get(value_field)
        if v is None and agg != "count":
            continue
        key = (*(r.get(f) for f in key_fields), wk)
        buckets[key].append(_num(v))

    reducer = _REDUCERS[agg]
    out = []
    for key, vals in sorted(buckets.items(), key=lambda kv: str(kv[0])):
        row = {f: key[i] for i, f in enumerate(key_fields)}
        row["window_start"] = key[-1]
        row["grain"] = grain
        row[f"{value_field}_{agg}"] = reducer(vals)
        row["count"] = len(vals)
        out.append(row)
    return out


def _num(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


_REDUCERS: dict[str, Callable[[list[float]], float]] = {
    "mean": lambda v: round(sum(v) / len(v), 6) if v else 0.0,
    "sum": lambda v: round(sum(v), 6),
    "min": lambda v: min(v) if v else 0.0,
    "max": lambda v: max(v) if v else 0.0,
    "count": lambda v: float(len(v)),
}
