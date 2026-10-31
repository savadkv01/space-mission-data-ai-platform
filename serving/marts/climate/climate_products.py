"""Climate / dust / air-quality serving marts — business-ready wide tables (Phase 11b).

These builders sit on the Phase 9b climate Gold marts
(``transformation.batch.climate_silver_to_gold``) and shape them into **data
products**: denormalized, business-named, dashboard- and API-ready rows that
avoid runtime joins. Each function mirrors a dbt model in
``serving/dbt/models/climate`` so the Python and SQL serving paths share one
definition, exactly like the MVP products in ``serving/marts/serving_marts.py``.

Grain and field names track the real Gold output exactly (see
``docs/data-modeling/climate/03-gold-marts.md`` and
``transformation/batch/climate_silver_to_gold.py``). All products are at
**AOI-date grain** and reuse the conformed ``dim_aoi`` semantic dimension, so a
single serving row is self-describing for BI (12b), API (16), and ML (14).

The band / flag classifications here are pass-throughs of the canonical Gold
columns; where a serving row must derive a display band it reuses the exact
thresholds registered in ``serving/marts/semantic.py`` and
``docs/data-modeling/climate/05-kpi-thresholds.md`` — no divergent formulas.

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
# 1. Air-Quality data product
# --------------------------------------------------------------------------- #

def serve_air_quality_daily(air_quality_rows: list[dict[str, Any]],
                            aoi_dim: list[dict[str, Any]] | None = None,
                            ) -> list[dict[str, Any]]:
    """Air-Quality data product.

    Source: ``fact_air_quality_daily`` (Gold). Enriches each AOI/day row with the
    AOI display name/area (``dim_aoi``) and surfaces the pre-computed pollutant
    means/maxes, per-pollutant AQI, worst-pollutant ``aqi_band`` and WHO
    ``exceedance_flag`` so a single row is self-describing for the weather /
    air-quality dashboards and the ``/analytics/air-quality`` API.
    """
    aoi_idx = _index_dim(aoi_dim, "aoi_key")
    out = []
    for r in air_quality_rows:
        aoi_key = r.get("aoi_key")
        dim = aoi_idx.get(aoi_key, {})
        out.append({
            "aoi_key": aoi_key,
            "aoi_name": dim.get("aoi_name"),
            "date_key": r.get("date_key"),
            "pm25_mean": r.get("pm25_mean"),
            "pm25_max": r.get("pm25_max"),
            "pm10_mean": r.get("pm10_mean"),
            "pm10_max": r.get("pm10_max"),
            "no2_column_mean": r.get("no2_column_mean"),
            "so2_column_mean": r.get("so2_column_mean"),
            "co_column_mean": r.get("co_column_mean"),
            "o3_column_mean": r.get("o3_column_mean"),
            "station_count": r.get("station_count", 0),
            "aqi_pm25": r.get("aqi_pm25"),
            "aqi_pm10": r.get("aqi_pm10"),
            "aqi_band": r.get("aqi_band"),
            "exceedance_flag": bool(r.get("exceedance_flag")),
            "area_km2": dim.get("area_km2"),
        })
    return sorted(out, key=lambda x: (x["aoi_key"] or "", x["date_key"] or ""))


# --------------------------------------------------------------------------- #
# 2. Dust-Event data product
# --------------------------------------------------------------------------- #

def serve_dust_event_daily(dust_rows: list[dict[str, Any]],
                           aoi_dim: list[dict[str, Any]] | None = None,
                           ) -> list[dict[str, Any]]:
    """Dust-Event data product.

    Source: ``fact_dust_event_daily`` (Gold). Surfaces AOD mean/max, UV aerosol
    index, dust-severity band, corroborated ``dust_flag`` and the wind /
    corridor transport context, enriched with AOI display metadata for the dust
    dashboard and API.
    """
    aoi_idx = _index_dim(aoi_dim, "aoi_key")
    out = []
    for r in dust_rows:
        aoi_key = r.get("aoi_key")
        dim = aoi_idx.get(aoi_key, {})
        out.append({
            "aoi_key": aoi_key,
            "aoi_name": dim.get("aoi_name"),
            "date_key": r.get("date_key"),
            "aod_mean": r.get("aod_mean"),
            "aod_max": r.get("aod_max"),
            "uv_aerosol_index_mean": r.get("uv_aerosol_index_mean"),
            "wind_speed_mean": r.get("wind_speed_mean"),
            "wind_dir_dominant": r.get("wind_dir_dominant"),
            "corridor_aod_max": r.get("corridor_aod_max"),
            "valid_fraction": r.get("valid_fraction"),
            "dust_severity_band": r.get("dust_severity_band"),
            "dust_severity_label": _dust_label(r.get("dust_severity_band")),
            "dust_flag": bool(r.get("dust_flag")),
            "transport_flag": bool(r.get("transport_flag")),
            "area_km2": dim.get("area_km2"),
        })
    return sorted(out, key=lambda x: (x["aoi_key"] or "", x["date_key"] or ""))


#: Display labels for the AOD dust-severity band (docs/data-modeling/climate/05).
_DUST_LABELS = {0: "Clear", 1: "Hazy", 2: "Dusty", 3: "Heavy dust", 4: "Severe"}


def _dust_label(band: Any) -> str:
    """Business-friendly dust-severity label from the numeric AOD band."""
    if band is None:
        return "unknown"
    return _DUST_LABELS.get(int(band), "unknown")


# --------------------------------------------------------------------------- #
# 3. Climate-Indicator data product
# --------------------------------------------------------------------------- #

def serve_climate_indicator_daily(climate_rows: list[dict[str, Any]],
                                  aoi_dim: list[dict[str, Any]] | None = None,
                                  vegetation_rows: list[dict[str, Any]] | None = None,
                                  ) -> list[dict[str, Any]]:
    """Climate-Indicator data product.

    Sources: ``fact_climate_indicator_daily`` and
    ``fact_vegetation_health_daily`` (Gold). Vegetation values are joined on
    AOI and date; unmatched observations stay null.
    """
    aoi_idx = _index_dim(aoi_dim, "aoi_key")
    vegetation_idx = {
        (row.get("aoi_key"), row.get("date_key")): row
        for row in vegetation_rows or []
        if row.get("aoi_key") is not None and row.get("date_key") is not None
    }
    out = []
    for r in climate_rows:
        aoi_key = r.get("aoi_key")
        date_key = r.get("date_key")
        dim = aoi_idx.get(aoi_key, {})
        vegetation = vegetation_idx.get((aoi_key, date_key), {})
        out.append({
            "aoi_key": aoi_key,
            "aoi_name": dim.get("aoi_name"),
            "date_key": date_key,
            "lst_c": r.get("lst_c"),
            "lst_anomaly_c": r.get("lst_anomaly_c"),
            "sst_c": r.get("sst_c"),
            "sst_anomaly_c": r.get("sst_anomaly_c"),
            "ndvi_mean": vegetation.get("ndvi_mean"),
            "evi_mean": vegetation.get("evi_mean"),
            "ndwi_mean": r.get("ndwi_mean"),
            "tree_cover_loss_ha": r.get("tree_cover_loss_ha"),
            "desertification_proxy": r.get("desertification_proxy"),
            "lst_anomaly_band": r.get("lst_anomaly_band"),
            "lst_anomaly_label": _lst_label(r.get("lst_anomaly_band")),
            "warming_flag": bool(r.get("warming_flag")),
            "desertification_flag": bool(r.get("desertification_flag")),
            "area_km2": dim.get("area_km2"),
        })
    return sorted(out, key=lambda x: (x["aoi_key"] or "", x["date_key"] or ""))


#: Display labels for the LST-anomaly band (docs/data-modeling/climate/05).
_LST_LABELS = {-1: "Cooler", 0: "Normal", 1: "Warm", 2: "Hot", 3: "Extreme"}


def _lst_label(band: Any) -> str:
    """Business-friendly warming label from the numeric LST-anomaly band."""
    if band is None:
        return "unknown"
    return _LST_LABELS.get(int(band), "unknown")


# --------------------------------------------------------------------------- #
# 4. Vegetation-Health data product
# --------------------------------------------------------------------------- #

def serve_vegetation_health_daily(vegetation_rows: list[dict[str, Any]],
                                  aoi_dim: list[dict[str, Any]] | None = None,
                                  ) -> list[dict[str, Any]]:
    """Vegetation-Health data product.

    Source: ``fact_vegetation_health_daily`` (Gold). Surfaces NDVI/EVI, the
    30-day NDVI trend, the NDVI health band and the ``crop_stress_flag`` (low +
    declining NDVI), enriched with AOI metadata for the agriculture / land
    dashboards.
    """
    aoi_idx = _index_dim(aoi_dim, "aoi_key")
    out = []
    for r in vegetation_rows:
        aoi_key = r.get("aoi_key")
        dim = aoi_idx.get(aoi_key, {})
        trend = r.get("ndvi_trend_30d")
        out.append({
            "aoi_key": aoi_key,
            "aoi_name": dim.get("aoi_name"),
            "date_key": r.get("date_key"),
            "ndvi_mean": r.get("ndvi_mean"),
            "ndvi_max": r.get("ndvi_max"),
            "evi_mean": r.get("evi_mean"),
            "ndvi_trend_30d": trend,
            "ndvi_trend_dir": _trend_dir(trend),
            "valid_pixel_fraction": r.get("valid_pixel_fraction"),
            "ndvi_health_band": r.get("ndvi_health_band"),
            "ndvi_health_label": _ndvi_label(r.get("ndvi_health_band")),
            "crop_stress_flag": bool(r.get("crop_stress_flag")),
            "area_km2": dim.get("area_km2"),
        })
    return sorted(out, key=lambda x: (x["aoi_key"] or "", x["date_key"] or ""))


#: Display labels for the NDVI health band (docs/data-modeling/climate/05).
_NDVI_LABELS = {0: "Bare / water", 1: "Sparse", 2: "Moderate", 3: "Healthy", 4: "Dense"}


def _ndvi_label(band: Any) -> str:
    """Business-friendly vegetation-health label from the numeric NDVI band."""
    if band is None:
        return "unknown"
    return _NDVI_LABELS.get(int(band), "unknown")


def _trend_dir(trend: Any) -> str:
    """Coarse direction of the 30-day NDVI slope for dashboard arrows."""
    if trend is None:
        return "flat"
    if trend > 0:
        return "improving"
    if trend < 0:
        return "declining"
    return "flat"
