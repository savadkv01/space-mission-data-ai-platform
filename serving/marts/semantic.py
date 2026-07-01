"""Semantic layer — the single source of business metric definitions (Task 3).

The semantic layer decouples *business meaning* from *physical storage*. Every
consumer (BI, API, ML, RAG) reads the same metric definitions so a KPI such as
"corroboration rate" means exactly one thing everywhere.

This module holds:

* ``DIMENSIONS`` — standard conformed dimensions and their business keys.
* ``METRICS``    — the metric registry: business name, grain, and a pure-Python
  reducer over serving rows. Reducers are the canonical definition mirrored by
  the dbt semantic models and the ``semantic/kpi-catalog.md`` documentation.
* ``compute_kpis`` — evaluate a set of metrics over rows, returning a KPI dict.

Keeping the reducers here (not scattered across dashboards or endpoints) is what
prevents metric drift between teams.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

Rows = list[dict[str, Any]]

# --------------------------------------------------------------------------- #
# Conformed dimensions (Task 3 — standard dimensions)
# --------------------------------------------------------------------------- #

DIMENSIONS: dict[str, dict[str, str]] = {
    "dim_date": {"key": "date_key", "grain": "calendar day (UTC)"},
    "dim_aoi": {"key": "aoi_key", "grain": "Copernicus-EMS activation footprint"},
    "dim_geo": {"key": "geo_key", "grain": "quantized lat/lon grid cell"},
    "dim_vessel": {"key": "vessel_key", "grain": "vessel identity (MMSI/IMO)"},
    "dim_provider": {"key": "provider_key", "grain": "launch/data provider"},
    "dim_satellite": {"key": "sat_key", "grain": "spacecraft (sim track)"},
}


# --------------------------------------------------------------------------- #
# Metric registry (Task 3 — standard measures + KPI catalogue)
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Metric:
    """A business metric definition.

    ``reducer`` is the canonical, storage-independent computation over a list of
    serving rows. It is the authority the dbt models and docs must match.
    """

    name: str
    unit: str
    grain: str
    description: str
    reducer: Callable[[Rows], float | None]


def _sum(field: str) -> Callable[[Rows], float | None]:
    return lambda rows: sum(r.get(field, 0) or 0 for r in rows)


def _mean(field: str) -> Callable[[Rows], float | None]:
    def fn(rows: Rows) -> float | None:
        vals = [r.get(field) for r in rows if r.get(field) is not None]
        return round(sum(vals) / len(vals), 4) if vals else None
    return fn


def _rate(flag_field: str) -> Callable[[Rows], float | None]:
    def fn(rows: Rows) -> float | None:
        n = len(rows)
        return round(sum(1 for r in rows if r.get(flag_field)) / n, 4) if n else None
    return fn


METRICS: dict[str, Metric] = {
    "total_fire_detections": Metric(
        "Total Fire Detections", "count", "aoi/day",
        "Sum of FIRMS/VIIRS thermal detections attributed to AOIs.",
        _sum("detections")),
    "mean_fire_frp": Metric(
        "Mean Fire Radiative Power", "MW", "aoi/day",
        "Average fire radiative power across wildfire detections.",
        _mean("mean_frp")),
    "flood_day_rate": Metric(
        "Flood Day Rate", "ratio", "aoi/day",
        "Fraction of AOI-days flagged as open water by NDWI.",
        _rate("flood_flag")),
    "suspicious_vessel_rate": Metric(
        "Suspicious Vessel Rate", "ratio", "vessel/day",
        "Fraction of vessel-days flagged with obscured identity.",
        _rate("suspicious_flag")),
    "searchable_scene_rate": Metric(
        "Searchable Scene Rate", "ratio", "scene",
        "Fraction of catalog scenes that are fully searchable.",
        _rate("is_searchable")),
    "ems_corroboration_rate": Metric(
        "EMS Corroboration Rate", "ratio", "aoi",
        "Fraction of EMS activation AOIs corroborated by independent detections.",
        _rate("corroborated")),
    # Simulation Track (post-MVP demonstrator)
    "mean_satellite_health": Metric(
        "Mean Satellite Health", "score", "sat/day",
        "Average satellite health score (sim track).",
        _mean("health_score")),
    "launch_success_rate": Metric(
        "Launch Success Rate", "ratio", "provider/month",
        "Weighted mean monthly launch success rate (sim track).",
        _mean("success_rate")),
}


def compute_kpis(rows: Rows, metric_names: list[str]) -> dict[str, float | None]:
    """Evaluate the named metrics over ``rows`` using the canonical reducers.

    Raises ``KeyError`` on an unknown metric so misspelled KPIs fail fast rather
    than silently returning nothing — a core semantic-consistency guarantee.
    """
    return {name: METRICS[name].reducer(rows) for name in metric_names}
