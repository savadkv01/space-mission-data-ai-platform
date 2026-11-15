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
# Evidence states
# --------------------------------------------------------------------------- #
# Gold flags are booleans, so a missing measurement and an observed negative
# both read ``False``. Serving separates them: ``<flag>_status`` is one of
# EVIDENCE_STATUSES and the serving flag is ``True`` / ``False`` only when the
# evidence decides it (``None`` otherwise). Mirrored in the climate dbt models.

EVIDENCE_STATUSES = ("positive", "negative", "inconclusive", "not_evaluated")

#: Gold dust / transport rule thresholds
#: (``transformation.batch.climate_silver_to_gold``; parity pinned by tests).
DUST_AOD_THRESHOLD = 0.5
DUST_UV_AI_THRESHOLD = 1.0
#: Gold ``crop_stress_flag`` NDVI ceiling (low NDVI AND declining trend).
CROP_STRESS_NDVI_THRESHOLD = 0.3


def _evidence_status(flag: Any, *, negative: bool, observed: bool) -> str:
    """``positive`` if the Gold rule fired; ``negative`` only if the available
    measurements rule it out; ``inconclusive`` if some but not enough evidence;
    ``not_evaluated`` if no supporting measurement exists."""
    if flag:
        return "positive"
    if negative:
        return "negative"
    return "inconclusive" if observed else "not_evaluated"


def _decided_flag(status: str) -> bool | None:
    return {"positive": True, "negative": False}.get(status)


def _below(value: Any, threshold: float) -> bool:
    return value is not None and value < threshold


def _pm_coverage(pm25: Any, pm10: Any) -> str:
    if pm25 is not None and pm10 is not None:
        return "pm25_and_pm10"
    if pm25 is not None:
        return "pm25_only"
    if pm10 is not None:
        return "pm10_only"
    return "none"


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

    ``exceedance_flag`` is an OR over PM2.5 / PM10, so it is ``False`` only when
    both are observed below guideline; missing PM is ``inconclusive`` /
    ``not_evaluated`` (``None``), never "clean air". A null ``aqi_band`` means
    no surface PM measurement, not "Good".
    """
    aoi_idx = _index_dim(aoi_dim, "aoi_key")
    out = []
    for r in air_quality_rows:
        aoi_key = r.get("aoi_key")
        dim = aoi_idx.get(aoi_key, {})
        pm25, pm10 = r.get("pm25_mean"), r.get("pm10_mean")
        status = _evidence_status(
            r.get("exceedance_flag"),
            negative=pm25 is not None and pm10 is not None,
            observed=pm25 is not None or pm10 is not None,
        )
        out.append({
            "aoi_key": aoi_key,
            "aoi_name": dim.get("aoi_name"),
            "region": dim.get("region"),
            "date_key": r.get("date_key"),
            "pm25_mean": pm25,
            "pm25_max": r.get("pm25_max"),
            "pm10_mean": pm10,
            "pm10_max": r.get("pm10_max"),
            "no2_column_mean": r.get("no2_column_mean"),
            "so2_column_mean": r.get("so2_column_mean"),
            "co_column_mean": r.get("co_column_mean"),
            "o3_column_mean": r.get("o3_column_mean"),
            "station_count": r.get("station_count", 0),
            "aqi_pm25": r.get("aqi_pm25"),
            "aqi_pm10": r.get("aqi_pm10"),
            "aqi_band": r.get("aqi_band"),
            "aqi_standard": r.get("aqi_standard"),
            "exceedance_flag": _decided_flag(status),
            "exceedance_status": status,
            "pm_coverage": _pm_coverage(pm25, pm10),
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

    Both rules are AND rules, so one observed sub-threshold component is a
    negative; missing components otherwise yield ``inconclusive`` /
    ``not_evaluated`` (flag ``None``). ``transport_flag`` remains a heuristic
    (other-AOI AOD + positive wind), not an established dust pathway.
    """
    aoi_idx = _index_dim(aoi_dim, "aoi_key")
    out = []
    for r in dust_rows:
        aoi_key = r.get("aoi_key")
        dim = aoi_idx.get(aoi_key, {})
        aod, uv = r.get("aod_mean"), r.get("uv_aerosol_index_mean")
        corridor, wind = r.get("corridor_aod_max"), r.get("wind_speed_mean")
        dust_status = _evidence_status(
            r.get("dust_flag"),
            negative=_below(aod, DUST_AOD_THRESHOLD) or _below(uv, DUST_UV_AI_THRESHOLD),
            observed=aod is not None or uv is not None,
        )
        transport_status = _evidence_status(
            r.get("transport_flag"),
            negative=_below(corridor, DUST_AOD_THRESHOLD) or (wind is not None and wind <= 0),
            observed=corridor is not None or wind is not None,
        )
        out.append({
            "aoi_key": aoi_key,
            "aoi_name": dim.get("aoi_name"),
            "region": dim.get("region"),
            "date_key": r.get("date_key"),
            "aod_mean": aod,
            "aod_max": r.get("aod_max"),
            "uv_aerosol_index_mean": uv,
            "wind_speed_mean": wind,
            "wind_dir_dominant": r.get("wind_dir_dominant"),
            "corridor_aod_max": corridor,
            "valid_fraction": r.get("valid_fraction"),
            "dust_severity_band": r.get("dust_severity_band"),
            "dust_severity_label": _dust_label(r.get("dust_severity_band")),
            "dust_flag": _decided_flag(dust_status),
            "dust_status": dust_status,
            "transport_flag": _decided_flag(transport_status),
            "transport_status": transport_status,
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

    ``warming_flag`` is an OR over LST / SST anomalies, so ``False`` requires
    both anomalies observed; ``desertification_flag`` requires the proxy. Absent
    measurements are ``inconclusive`` / ``not_evaluated`` (flag ``None``), never
    "no warming". ``tree_cover_loss_ha`` has no ingested source and stays null.
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
        lst_anom, sst_anom = r.get("lst_anomaly_c"), r.get("sst_anomaly_c")
        proxy = r.get("desertification_proxy")
        warming_status = _evidence_status(
            r.get("warming_flag"),
            negative=lst_anom is not None and sst_anom is not None,
            observed=lst_anom is not None or sst_anom is not None,
        )
        desertification_status = _evidence_status(
            r.get("desertification_flag"), negative=proxy is not None, observed=proxy is not None,
        )
        out.append({
            "aoi_key": aoi_key,
            "aoi_name": dim.get("aoi_name"),
            "region": dim.get("region"),
            "date_key": date_key,
            "lst_c": r.get("lst_c"),
            "lst_anomaly_c": lst_anom,
            "sst_c": r.get("sst_c"),
            "sst_anomaly_c": sst_anom,
            "ndvi_mean": vegetation.get("ndvi_mean"),
            "evi_mean": vegetation.get("evi_mean"),
            "ndwi_mean": r.get("ndwi_mean"),
            "tree_cover_loss_ha": r.get("tree_cover_loss_ha"),
            "desertification_proxy": proxy,
            "lst_anomaly_band": r.get("lst_anomaly_band"),
            "lst_anomaly_label": _lst_label(r.get("lst_anomaly_band")),
            "warming_flag": _decided_flag(warming_status),
            "warming_status": warming_status,
            "desertification_flag": _decided_flag(desertification_status),
            "desertification_status": desertification_status,
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

    A missing trend (fewer than two NDVI observations) is ``unknown``, never
    ``flat``. ``crop_stress_flag`` is an AND rule, so one observed component at
    or above its threshold is a negative; otherwise missing inputs yield
    ``inconclusive`` / ``not_evaluated`` (flag ``None``). A positive is a
    low/declining NDVI signal, not a verified crop-stress event.
    """
    aoi_idx = _index_dim(aoi_dim, "aoi_key")
    out = []
    for r in vegetation_rows:
        aoi_key = r.get("aoi_key")
        dim = aoi_idx.get(aoi_key, {})
        ndvi = r.get("ndvi_mean")
        trend = r.get("ndvi_trend_30d")
        crop_status = _evidence_status(
            r.get("crop_stress_flag"),
            negative=(ndvi is not None and ndvi >= CROP_STRESS_NDVI_THRESHOLD)
            or (trend is not None and trend >= 0),
            observed=ndvi is not None or trend is not None,
        )
        out.append({
            "aoi_key": aoi_key,
            "aoi_name": dim.get("aoi_name"),
            "region": dim.get("region"),
            "date_key": r.get("date_key"),
            "ndvi_mean": ndvi,
            "ndvi_max": r.get("ndvi_max"),
            "evi_mean": r.get("evi_mean"),
            "ndvi_trend_30d": trend,
            "ndvi_trend_dir": _trend_dir(trend),
            "valid_pixel_fraction": r.get("valid_pixel_fraction"),
            "ndvi_health_band": r.get("ndvi_health_band"),
            "ndvi_health_label": _ndvi_label(r.get("ndvi_health_band")),
            "crop_stress_flag": _decided_flag(crop_status),
            "crop_stress_status": crop_status,
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
    """Coarse direction of the 30-day NDVI slope for dashboard arrows.

    ``unknown`` when no slope could be computed; only a computed zero is ``flat``.
    """
    if trend is None:
        return "unknown"
    if trend > 0:
        return "improving"
    if trend < 0:
        return "declining"
    return "flat"
