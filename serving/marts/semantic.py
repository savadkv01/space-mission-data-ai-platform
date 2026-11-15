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
    # Phase 11b climate extension (conformed to the same bus; not forked).
    "dim_pollutant": {"key": "pollutant_code", "grain": "pollutant / aerosol species"},
    "dim_climate_indicator": {"key": "indicator_code", "grain": "climate / vegetation indicator"},
}


# --------------------------------------------------------------------------- #
# Climate reference dimensions (Phase 11b — from data-modeling 06b/04, 05)
# --------------------------------------------------------------------------- #
# Canonical, business-friendly attributes for the two new conformed dimensions.
# Single-sourced here and mirrored by the dbt models
# ``serving/dbt/models/semantic/dim_{pollutant,climate_indicator}.sql`` and the
# raw DDL in ``serving/sql/climate/``.

AQI_BREAKPOINTS: dict[str, list[dict[str, Any]]] = {
    "PM25": [
        {"aqi_low": 0, "aqi_high": 50, "value_low": 0.0, "value_high": 12.0, "label": "Good"},
        {"aqi_low": 51, "aqi_high": 100, "value_low": 12.1, "value_high": 35.4, "label": "Moderate"},
        {"aqi_low": 101, "aqi_high": 150, "value_low": 35.5, "value_high": 55.4, "label": "Unhealthy (sensitive)"},
        {"aqi_low": 151, "aqi_high": 200, "value_low": 55.5, "value_high": 150.4, "label": "Unhealthy"},
        {"aqi_low": 201, "aqi_high": 300, "value_low": 150.5, "value_high": 250.4, "label": "Very Unhealthy"},
        {"aqi_low": 301, "aqi_high": 500, "value_low": 250.5, "value_high": 500.4, "label": "Hazardous"},
    ],
    "PM10": [
        {"aqi_low": 0, "aqi_high": 50, "value_low": 0.0, "value_high": 54.0, "label": "Good"},
        {"aqi_low": 51, "aqi_high": 100, "value_low": 55.0, "value_high": 154.0, "label": "Moderate"},
        {"aqi_low": 101, "aqi_high": 150, "value_low": 155.0, "value_high": 254.0, "label": "Unhealthy (sensitive)"},
        {"aqi_low": 151, "aqi_high": 200, "value_low": 255.0, "value_high": 354.0, "label": "Unhealthy"},
        {"aqi_low": 201, "aqi_high": 300, "value_low": 355.0, "value_high": 424.0, "label": "Very Unhealthy"},
        {"aqi_low": 301, "aqi_high": 500, "value_low": 425.0, "value_high": 604.0, "label": "Hazardous"},
    ],
}

#: AOD load bands for any aerosol type (D-07): dust wording is reserved for rows
#: whose dust rule is positive (serving ``dust_severity_label``).
AOD_SEVERITY_BANDS: list[dict[str, Any]] = [
    {"band": 0, "label": "Clear", "value_low": 0.0, "value_high": 0.2},
    {"band": 1, "label": "Hazy", "value_low": 0.2, "value_high": 0.5},
    {"band": 2, "label": "Elevated", "value_low": 0.5, "value_high": 1.0},
    {"band": 3, "label": "High", "value_low": 1.0, "value_high": 2.0},
    {"band": 4, "label": "Very high", "value_low": 2.0, "value_high": 5.0},
]

LST_ANOMALY_BANDS: list[dict[str, Any]] = [
    {"band": -1, "label": "Cooler", "value_low": None, "value_high": -1.0},
    {"band": 0, "label": "Normal", "value_low": -1.0, "value_high": 1.0},
    {"band": 1, "label": "Warm", "value_low": 1.0, "value_high": 3.0},
    {"band": 2, "label": "Hot", "value_low": 3.0, "value_high": 5.0},
    {"band": 3, "label": "Extreme", "value_low": 5.0, "value_high": None},
]

NDVI_HEALTH_BANDS: list[dict[str, Any]] = [
    {"band": 0, "label": "Bare / water", "value_low": -1.0, "value_high": 0.1},
    {"band": 1, "label": "Sparse", "value_low": 0.1, "value_high": 0.3},
    {"band": 2, "label": "Moderate", "value_low": 0.3, "value_high": 0.5},
    {"band": 3, "label": "Healthy", "value_low": 0.5, "value_high": 0.7},
    {"band": 4, "label": "Dense", "value_low": 0.7, "value_high": 1.0},
]

POLLUTANTS: list[dict[str, Any]] = [
    {"pollutant_code": "PM25", "pollutant_name": "Fine Particulate Matter",
     "measure_type": "surface_concentration", "canonical_unit": "µg/m³",
     "aqi_scheme": "US_EPA", "aqi_breakpoints": AQI_BREAKPOINTS["PM25"],
     "severity_bands": [], "who_guideline": 15.0, "exceedance_threshold": 15.0},
    {"pollutant_code": "PM10", "pollutant_name": "Coarse Particulate Matter",
     "measure_type": "surface_concentration", "canonical_unit": "µg/m³",
     "aqi_scheme": "US_EPA", "aqi_breakpoints": AQI_BREAKPOINTS["PM10"],
     "severity_bands": [], "who_guideline": 45.0, "exceedance_threshold": 45.0},
    {"pollutant_code": "NO2", "pollutant_name": "Nitrogen Dioxide",
     "measure_type": "column_density", "canonical_unit": "mol/m²",
     "aqi_scheme": "n/a", "aqi_breakpoints": [], "severity_bands": [],
     "who_guideline": None, "exceedance_threshold": None},
    {"pollutant_code": "SO2", "pollutant_name": "Sulphur Dioxide",
     "measure_type": "column_density", "canonical_unit": "mol/m²",
     "aqi_scheme": "n/a", "aqi_breakpoints": [], "severity_bands": [],
     "who_guideline": None, "exceedance_threshold": None},
    {"pollutant_code": "CO", "pollutant_name": "Carbon Monoxide",
     "measure_type": "column_density", "canonical_unit": "mol/m²",
     "aqi_scheme": "n/a", "aqi_breakpoints": [], "severity_bands": [],
     "who_guideline": None, "exceedance_threshold": None},
    {"pollutant_code": "O3", "pollutant_name": "Ozone",
     "measure_type": "column_density", "canonical_unit": "mol/m²",
     "aqi_scheme": "n/a", "aqi_breakpoints": [], "severity_bands": [],
     "who_guideline": None, "exceedance_threshold": None},
    {"pollutant_code": "CH4", "pollutant_name": "Methane",
     "measure_type": "column_density", "canonical_unit": "ppb",
     "aqi_scheme": "n/a", "aqi_breakpoints": [], "severity_bands": [],
     "who_guideline": None, "exceedance_threshold": None},
    {"pollutant_code": "AOD", "pollutant_name": "Aerosol Optical Depth",
     "measure_type": "optical", "canonical_unit": "unitless",
     "aqi_scheme": "n/a", "aqi_breakpoints": [],
     "severity_bands": AOD_SEVERITY_BANDS,
     "who_guideline": None, "exceedance_threshold": 0.5},
]

CLIMATE_INDICATORS: list[dict[str, Any]] = [
    {"indicator_code": "LST", "indicator_name": "Land Surface Temperature",
     "unit": "°C", "source_family": "MODIS/Landsat", "native_cadence": "daily",
     "normal_range": None, "anomaly_bands": [], "requires_new_ingest": False},
    {"indicator_code": "LST_ANOM", "indicator_name": "LST Anomaly (same-DOY)",
     "unit": "°C", "source_family": "derived", "native_cadence": "daily",
     "normal_range": None, "anomaly_bands": LST_ANOMALY_BANDS, "requires_new_ingest": False},
    {"indicator_code": "SST", "indicator_name": "Sea Surface Temperature",
     "unit": "°C", "source_family": "OISST", "native_cadence": "daily",
     "normal_range": None, "anomaly_bands": [], "requires_new_ingest": False},
    {"indicator_code": "SST_ANOM", "indicator_name": "SST Anomaly (same-DOY)",
     "unit": "°C", "source_family": "derived", "native_cadence": "daily",
     "normal_range": None, "anomaly_bands": [], "requires_new_ingest": False},
    {"indicator_code": "NDVI", "indicator_name": "Vegetation Index (NDVI)",
     "unit": "index", "source_family": "Sentinel-2", "native_cadence": "16-day",
     "normal_range": [-1.0, 1.0], "anomaly_bands": NDVI_HEALTH_BANDS, "requires_new_ingest": False},
    {"indicator_code": "EVI", "indicator_name": "Enhanced Vegetation Index",
     "unit": "index", "source_family": "Sentinel-2", "native_cadence": "16-day",
     "normal_range": [-1.0, 1.0], "anomaly_bands": [], "requires_new_ingest": False},
    {"indicator_code": "NDWI", "indicator_name": "Water Index (NDWI)",
     "unit": "index", "source_family": "Sentinel-2", "native_cadence": "16-day",
     "normal_range": [-1.0, 1.0], "anomaly_bands": [], "requires_new_ingest": False},
    {"indicator_code": "TREE_LOSS", "indicator_name": "Tree-Cover Loss",
     "unit": "ha", "source_family": "GFW", "native_cadence": "annual",
     "normal_range": None, "anomaly_bands": [], "requires_new_ingest": False},
    {"indicator_code": "DESERT_PROXY", "indicator_name": "Desertification Proxy",
     "unit": "index", "source_family": "derived", "native_cadence": "daily",
     "normal_range": [0.0, 1.0], "anomaly_bands": [], "requires_new_ingest": False},
]


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


def _count_flag(flag_field: str) -> Callable[[Rows], float | None]:
    return lambda rows: sum(1 for r in rows if r.get(flag_field))


def _max(field: str) -> Callable[[Rows], float | None]:
    def fn(rows: Rows) -> float | None:
        vals = [r.get(field) for r in rows if r.get(field) is not None]
        return max(vals) if vals else None
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


# --------------------------------------------------------------------------- #
# Climate / dust / air-quality metrics (Phase 11b — from data-modeling 05b)
# --------------------------------------------------------------------------- #

CLIMATE_METRICS: dict[str, Metric] = {
    "aqi_pm25_mean": Metric(
        "Mean PM2.5 AQI", "index", "aoi/day",
        "Average EPA PM2.5 AQI over air-quality rows.",
        _mean("aqi_pm25")),
    "aqi_exceedance_days": Metric(
        "AQI Exceedance Days", "count", "aoi/day",
        "Count of AOI-days where a pollutant mean exceeds its WHO guideline.",
        _count_flag("exceedance_flag")),
    "dust_event_days": Metric(
        "Dust Event Days", "count", "aoi/day",
        "Count of AOI-days with a corroborated dust flag (AOD + UV AI).",
        _count_flag("dust_flag")),
    "aod_max": Metric(
        "Peak Aerosol Optical Depth", "unitless", "aoi/day",
        "Maximum daily AOD mean across dust rows.",
        _max("aod_mean")),
    "lst_anomaly_mean": Metric(
        "Mean LST Anomaly", "°C", "aoi/day",
        "Average land-surface-temperature anomaly vs same-DOY baseline.",
        _mean("lst_anomaly_c")),
    "warming_days": Metric(
        "Warming Days", "count", "aoi/day",
        "Count of AOI-days flagged as a warming anomaly (LST/SST threshold).",
        _count_flag("warming_flag")),
    "desertification_flag_days": Metric(
        "Desertification Days", "count", "aoi/day",
        "Count of AOI-days flagged by the desertification proxy.",
        _count_flag("desertification_flag")),
    "ndvi_health_mean": Metric(
        "Mean NDVI", "index", "aoi/day",
        "Average NDVI across vegetation-health rows.",
        _mean("ndvi_mean")),
    "crop_stress_days": Metric(
        "Crop-Stress Days", "count", "aoi/day",
        "Count of AOI-days where NDVI is low and declining.",
        _count_flag("crop_stress_flag")),
}

METRICS.update(CLIMATE_METRICS)


def compute_kpis(rows: Rows, metric_names: list[str]) -> dict[str, float | None]:
    """Evaluate the named metrics over ``rows`` using the canonical reducers.

    Raises ``KeyError`` on an unknown metric so misspelled KPIs fail fast rather
    than silently returning nothing — a core semantic-consistency guarantee.
    """
    return {name: METRICS[name].reducer(rows) for name in metric_names}
