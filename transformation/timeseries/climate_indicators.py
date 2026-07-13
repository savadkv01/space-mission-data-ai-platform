"""Derived climate indicators — anomalies, trends, composites (Phase 9b).

Extends the time-series engine (:mod:`transformation.timeseries.time_series`)
with the anomaly / trend / composite primitives the climate Gold marts need.
Pure-Python and dependency-free so the offline path and unit tests share one
definition with the Spark jobs (which apply the same windowed semantics).

These support Task 2 of Phase 9b — *derived* indicators from **already-ingested**
sources (NDVI/EVI/NDWI from ``obs_index``; LST/SST where present). No new
ingestion is introduced.
"""

from __future__ import annotations

from typing import Any

from transformation.timeseries.time_series import parse_ts


def day_of_year(value: Any) -> int | None:
    """Day-of-year (1..366) for a timestamp, used to align seasonal baselines."""
    ts = parse_ts(value)
    return ts.timetuple().tm_yday if ts else None


def same_doy_baseline(
    points: list[dict[str, Any]], value_field: str, ts_field: str = "event_ts"
) -> dict[int, float]:
    """Mean value per day-of-year — a seasonal baseline for anomaly detection.

    Grouping by day-of-year (rather than calendar date) lets an anomaly compare a
    reading against the *same time of year* across the historical window, which
    is how LST / SST anomalies are defined (docs/data-modeling/climate).
    """
    buckets: dict[int, list[float]] = {}
    for p in points:
        doy = day_of_year(p.get(ts_field))
        v = p.get(value_field)
        if doy is None or v is None:
            continue
        try:
            buckets.setdefault(doy, []).append(float(v))
        except (TypeError, ValueError):
            continue
    return {doy: round(sum(vals) / len(vals), 6) for doy, vals in buckets.items()}


def anomaly(value: float | None, baseline: float | None) -> float | None:
    """Difference of a value from its baseline (``None`` when either is missing)."""
    if value is None or baseline is None:
        return None
    return round(float(value) - float(baseline), 6)


def linear_trend(values: list[float]) -> float | None:
    """Ordinary-least-squares slope of ``values`` against their index.

    Used for the 30-day NDVI slope and the desertification NDVI-trend term.
    Returns ``None`` for fewer than two points; ``0.0`` for a flat series.
    """
    vals = [float(v) for v in values if v is not None]
    n = len(vals)
    if n < 2:
        return None
    mean_x = (n - 1) / 2.0
    mean_y = sum(vals) / n
    num = sum((i - mean_x) * (v - mean_y) for i, v in enumerate(vals))
    den = sum((i - mean_x) ** 2 for i in range(n))
    if den == 0:
        return 0.0
    return round(num / den, 6)


def velocity_of_change(values: list[float]) -> float | None:
    """First-difference velocity (last minus previous) of an ordered series.

    A feature-store-friendly "rate of change" signal (Task 4) — e.g. how fast
    AOD or NDVI is moving day over day.
    """
    vals = [float(v) for v in values if v is not None]
    if len(vals) < 2:
        return None
    return round(vals[-1] - vals[-2], 6)


def desertification_proxy(
    ndvi_trend: float | None, lst_anomaly_c: float | None
) -> float | None:
    """Composite desertification signal in ``[0, 1]`` (higher = more degradation).

    Combines a *declining* vegetation trend with a *positive* land-surface
    temperature anomaly — the two hallmarks of desert-margin degradation. Each
    term is normalised and clipped, then averaged. ``None`` when both drivers are
    absent (a single available driver still yields a proxy).
    """
    terms: list[float] = []
    if ndvi_trend is not None:
        # Negative NDVI slope -> degradation. Scale a -0.01/day slope to ~1.0.
        veg = max(0.0, min(1.0, -float(ndvi_trend) / 0.01))
        terms.append(veg)
    if lst_anomaly_c is not None:
        # +5 °C anomaly -> ~1.0.
        heat = max(0.0, min(1.0, float(lst_anomaly_c) / 5.0))
        terms.append(heat)
    if not terms:
        return None
    return round(sum(terms) / len(terms), 4)
