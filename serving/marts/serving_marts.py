"""Serving marts — business-ready wide tables built on Gold (Task 4).

These builders sit on the Phase 6 Gold marts (``transformation.batch.silver_to_gold``)
and shape them into **data products**: denormalized, business-named, dashboard-
and API-ready rows that avoid runtime joins. Each function mirrors a dbt model in
``serving/dbt/models`` so the Python and SQL serving paths share one definition.

Grain and field names track the real Gold output exactly (see
``docs/data-modeling/04-gold-layer.md``). MVP Earth-observation products are the
primary surface; Simulation-Track spacecraft products are marked ``sim`` and are
retained as a demonstrator only (ADR-09).

Everything here is pure-Python and infra-free so it unit-tests on any laptop.
"""

from __future__ import annotations

from typing import Any, Iterable

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _index_dim(dim_rows: Iterable[dict[str, Any]] | None, key: str) -> dict[Any, dict[str, Any]]:
    """Index a dimension list by its business key for O(1) enrichment."""
    if not dim_rows:
        return {}
    return {r.get(key): r for r in dim_rows if r.get(key) is not None}


# --------------------------------------------------------------------------- #
# MVP Earth-observation data products
# --------------------------------------------------------------------------- #

def serve_wildfire_daily(wildfire_aoi_rows: list[dict[str, Any]],
                         aoi_dim: list[dict[str, Any]] | None = None,
                         validation_rows: list[dict[str, Any]] | None = None,
                         ) -> list[dict[str, Any]]:
    """Wildfire Activity data product (UC-15).

    Source: ``kpi_wildfire_aoi_daily`` (Gold). Enriches each AOI/day row with the
    AOI display name/event metadata (``dim_aoi``) and the Copernicus-EMS
    cross-source corroboration flag (``kpi_aoi_validation``) so a single row is
    self-describing for dashboards and the ``/analytics/wildfire`` API.
    """
    aoi_idx = _index_dim(aoi_dim, "aoi_key")
    corroborated = {r.get("aoi_key") for r in (validation_rows or [])
                    if r.get("event_type") == "fire" and r.get("corroborated")}
    out = []
    for r in wildfire_aoi_rows:
        aoi_key = r.get("aoi_key")
        dim = aoi_idx.get(aoi_key, {})
        out.append({
            "aoi_key": aoi_key,
            "aoi_name": dim.get("aoi_name"),
            "date_key": r.get("date_key"),
            "detections": r.get("detections", 0),
            "mean_frp": r.get("mean_frp"),
            "max_frp": r.get("max_frp"),
            "area_km2": dim.get("area_km2"),
            "severity": _fire_severity(r.get("max_frp")),
            "ems_corroborated": aoi_key in corroborated,
        })
    return sorted(out, key=lambda x: (x["aoi_key"] or "", x["date_key"] or ""))


def _fire_severity(max_frp: Any) -> str:
    """Coarse operational severity band from peak fire radiative power (MW)."""
    if max_frp is None:
        return "unknown"
    if max_frp >= 100:
        return "extreme"
    if max_frp >= 30:
        return "high"
    if max_frp >= 10:
        return "moderate"
    return "low"


def serve_flood_daily(flood_aoi_rows: list[dict[str, Any]],
                      aoi_dim: list[dict[str, Any]] | None = None,
                      validation_rows: list[dict[str, Any]] | None = None,
                      ) -> list[dict[str, Any]]:
    """Flood Extent data product (UC-16).

    Source: ``kpi_flood_aoi_daily`` (Gold NDWI water statistics). Adds AOI display
    metadata and EMS corroboration so flood-day rows are BI/API ready.
    """
    aoi_idx = _index_dim(aoi_dim, "aoi_key")
    corroborated = {r.get("aoi_key") for r in (validation_rows or [])
                    if r.get("event_type") == "flood" and r.get("corroborated")}
    out = []
    for r in flood_aoi_rows:
        aoi_key = r.get("aoi_key")
        dim = aoi_idx.get(aoi_key, {})
        out.append({
            "aoi_key": aoi_key,
            "aoi_name": dim.get("aoi_name"),
            "date_key": r.get("date_key"),
            "ndwi_mean": r.get("ndwi_mean"),
            "ndwi_max": r.get("ndwi_max"),
            "valid_pixel_fraction": r.get("valid_pixel_fraction"),
            "flood_flag": bool(r.get("flood_flag")),
            "area_km2": dim.get("area_km2"),
            "ems_corroborated": aoi_key in corroborated,
        })
    return sorted(out, key=lambda x: (x["aoi_key"] or "", x["date_key"] or ""))


def serve_vessel_activity(vessel_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Maritime Vessel Activity data product (UC-18).

    Source: ``fact_vessel_activity`` (Gold). Surfaces the suspicious-identity
    heuristic and a review-priority band for the illegal-fishing triage workflow.
    """
    out = []
    for r in vessel_rows:
        suspicious = bool(r.get("suspicious_flag"))
        out.append({
            "vessel_key": r.get("vessel_key"),
            "date_key": r.get("date_key"),
            "transmissions": r.get("transmissions", 0),
            "flag": r.get("flag"),
            "vessel_type": r.get("vessel_type"),
            "active_span_days": r.get("active_span_days"),
            "suspicious_flag": suspicious,
            "review_priority": "high" if suspicious else "normal",
        })
    return sorted(out, key=lambda x: (x["vessel_key"] or "", x["date_key"] or ""))


def serve_scene_catalog(scene_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Imagery Catalog data product (UC-25).

    Source: ``fact_scene_catalog`` (Gold, 1 row/scene). Exposes searchability and
    a catalog-quality band for the metadata-management use case.
    """
    out = []
    for r in scene_rows:
        completeness = r.get("completeness_score")
        out.append({
            "scene_key": r.get("scene_key"),
            "date_key": r.get("date_key"),
            "collection": r.get("collection"),
            "provider": r.get("provider"),
            "platform": r.get("platform"),
            "geo_key": r.get("geo_key"),
            "cloud_cover": r.get("cloud_cover"),
            "completeness_score": completeness,
            "is_searchable": bool(r.get("is_searchable")),
            "quality_band": _catalog_band(completeness, r.get("is_searchable")),
        })
    return sorted(out, key=lambda x: x["scene_key"] or "")


def _catalog_band(completeness: Any, searchable: Any) -> str:
    """Catalog-quality band combining metadata completeness and searchability."""
    if not searchable:
        return "unlisted"
    if completeness is None:
        return "listed"
    if completeness >= 0.9:
        return "gold"
    if completeness >= 0.7:
        return "silver"
    return "bronze"


def serve_aoi_validation(validation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Detection Validation data product (UC-27 damage / QA).

    Source: ``kpi_aoi_validation``. Exposes EMS ground-truth corroboration as a
    trust signal for damage-assessment prioritization and detection QA.
    """
    out = []
    for r in validation_rows:
        out.append({
            "aoi_key": r.get("aoi_key"),
            "event_type": r.get("event_type"),
            "event_date": r.get("event_date"),
            "area_km2": r.get("area_km2"),
            "evidence_days": r.get("evidence_days", 0),
            "corroborated": bool(r.get("corroborated")),
            "trust": "corroborated" if r.get("corroborated") else "unconfirmed",
        })
    return sorted(out, key=lambda x: x["aoi_key"] or "")


# --------------------------------------------------------------------------- #
# Simulation-Track spacecraft data products (post-MVP demonstrator, ADR-09)
# --------------------------------------------------------------------------- #

def serve_satellite_health(health_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Satellite Health Summary data product (Sim Track).

    Source: ``fact_sat_health`` (synthetic telemetry). Adds a status band for the
    operations dashboard demonstrator.
    """
    out = []
    for r in health_rows:
        score = r.get("health_score")
        out.append({
            "sat_key": r.get("sat_key"),
            "date_key": r.get("date_key"),
            "samples": r.get("samples", 0),
            "health_score": score,
            "anomaly_density": r.get("anomaly_density"),
            "status": _health_status(score),
            "track": "sim",
        })
    return sorted(out, key=lambda x: (x["sat_key"] or "", x["date_key"] or ""))


def _health_status(score: Any) -> str:
    if score is None:
        return "unknown"
    if score >= 0.8:
        return "nominal"
    if score >= 0.5:
        return "degraded"
    return "critical"


def serve_launch_monthly(launch_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Launch Performance data product (Sim Track).

    Source: ``kpi_launch_monthly`` (synthetic). 1 row/provider/month.
    """
    out = []
    for r in launch_rows:
        out.append({
            "provider_key": r.get("provider_key"),
            "month_key": r.get("month_key"),
            "launches": r.get("launches", 0),
            "successes": r.get("successes", 0),
            "success_rate": r.get("success_rate"),
            "mean_delay_days": r.get("mean_delay_days"),
            "track": "sim",
        })
    return sorted(out, key=lambda x: (x["provider_key"] or "", x["month_key"] or ""))


def serve_weather_impact(weather_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Space Weather Impact data product (Sim Track).

    Source: ``fact_weather_impact`` (synthetic). 1 row/day correlating Kp index
    with telemetry anomaly rate.
    """
    out = []
    for r in weather_rows:
        out.append({
            "date_key": r.get("date_key"),
            "max_kp_index": r.get("max_kp_index"),
            "mean_kp_index": r.get("mean_kp_index"),
            "storm_events": r.get("storm_events", 0),
            "anomaly_rate": r.get("anomaly_rate"),
            "storm_day": bool((r.get("max_kp_index") or 0) >= 5),
            "track": "sim",
        })
    return sorted(out, key=lambda x: x["date_key"] or "")
