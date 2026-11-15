"""Climate / dust / air-quality quality suites (Phase 10b — Data Quality).

Declarative quality-gate suites for the climate expansion Silver/Gold entities
(Phase 9b), built on the same dependency-free expectation framework used by the
Earth-observation suites in :mod:`transformation.quality.eo_suites`
(``transformation.cleaning.validation_framework`` — a laptop-friendly analogue of
Great Expectations). Each ``*_suite`` returns a list of ``Expectation`` objects;
run them with ``run_checkpoint`` to gate a Silver or Gold batch.

Field names mirror the actual Silver/Gold outputs produced by
``transformation.cleaning.climate.*`` and
``transformation.batch.climate_silver_to_gold``.

Severity model: ``critical`` expectations fail (hold) a batch; ``warn``
expectations log a signal but allow promotion.

In-scope entities (Phase 6b/9b):

* Silver — ``obs_air_quality``, ``obs_aerosol``, ``obs_atmos_column``, ``obs_wind``
* Gold   — ``fact_air_quality_daily``, ``fact_dust_event_daily``,
  ``fact_climate_indicator_daily``, ``fact_vegetation_health_daily``
"""

from __future__ import annotations

from typing import Any, Callable

from transformation.cleaning.validation_framework import (
    Expectation,
    expect_not_null,
    expect_row_count_min,
    expect_unique,
    expect_value_in_range,
)

# A large finite upper bound for "non-negative" numeric checks.
_MAX = 1e12

# --- Controlled vocabularies (align with dim_pollutant / dim_climate_indicator
#     and docs/data-modeling/climate/) ---------------------------------------

#: Canonical surface-pollutant codes (``obs_air_quality.pollutant_code``).
POLLUTANT_CODES = {"PM25", "PM10", "NO2", "SO2", "CO", "O3", "BC"}

#: TROPOMI trace-gas / aerosol-index products (``obs_atmos_column.gas_code``).
GAS_CODES = {"NO2", "SO2", "CO", "O3", "CH4", "AER_AI"}

#: Canonical atmospheric-column units (``obs_atmos_column.unit_std``).
COLUMN_UNITS = {"mol/m2", "ppb", "unitless"}

#: NASA POWER daily wind parameters and units.
WIND_UNITS = {"WS2M": "m/s", "WD2M": "degree"}

#: Silver quality-flag vocabulary across climate entities.
QUALITY_FLAGS = {"valid", "suspect", "low_coverage"}

#: AQI category labels (``fact_air_quality_daily.aqi_band``): US EPA (UAE-GULF)
#: plus CPCB NAQI (INDIA); ``aqi_standard`` says which scheme applies.
AQI_BANDS = {
    "Good", "Moderate", "Unhealthy (sensitive)", "Unhealthy",
    "Very Unhealthy", "Hazardous",
    "Satisfactory", "Poor", "Very Poor", "Severe",
}

# --- Local expectation helpers ---------------------------------------------


def expect_predicate(name: str, predicate: Callable[[list[dict[str, Any]]], bool],
                     severity: str = "critical", description: str = "") -> Expectation:
    """Wrap an arbitrary batch-level predicate as an ``Expectation``."""
    return Expectation(name=name, predicate=predicate, severity=severity,
                       description=description)


def expect_value_in_set(field: str, allowed: set[Any], severity: str = "critical",
                        allow_null: bool = True) -> Expectation:
    """Every ``field`` value must be drawn from ``allowed`` (nulls optional)."""
    def _check(rows: list[dict[str, Any]]) -> bool:
        for r in rows:
            v = r.get(field)
            if v is None:
                if allow_null:
                    continue
                return False
            if v not in allowed:
                return False
        return True

    return Expectation(
        name=f"enum:{field}",
        predicate=_check,
        severity=severity,
        description=f"{field} in {sorted(str(a) for a in allowed)}.",
    )


def expect_non_negative(field: str, severity: str = "critical") -> Expectation:
    """``field`` is null or >= 0 (physical non-negativity)."""
    return expect_value_in_range(field, 0, _MAX, severity=severity)


# ===========================================================================
# Silver suites
# ===========================================================================


def silver_air_quality_suite() -> list[Expectation]:
    """``obs_air_quality`` — OpenAQ surface pollutant readings (Phase 9b)."""
    return [
        expect_row_count_min(1),
        expect_not_null("air_quality_key"),
        expect_not_null("event_ts"),
        expect_not_null("pollutant_code"),
        expect_not_null("geo_key"),
        expect_unique(["air_quality_key"]),
        # Enum / vocabulary.
        expect_value_in_set("pollutant_code", POLLUTANT_CODES),
        expect_value_in_set("quality_flag", QUALITY_FLAGS),
        # Geospatial bounds.
        expect_value_in_range("latitude", -90, 90),
        expect_value_in_range("longitude", -180, 180),
        # Non-negative concentrations (µg/m³ or mg/m³ canonical).
        expect_value_in_range("value_std", 0, _MAX),
        expect_value_in_range("value_raw", 0, _MAX),
        # Pollutant-specific plausibility caps (µg/m³ for PM; warn only).
        expect_predicate(
            "range:pm25_plausible",
            lambda rows: all(
                r.get("value_std") is None or float(r["value_std"]) <= 1000
                for r in rows if r.get("pollutant_code") == "PM25"
            ),
            severity="warn",
            description="PM2.5 value_std <= 1000 µg/m³ (plausibility).",
        ),
        expect_predicate(
            "range:pm10_plausible",
            lambda rows: all(
                r.get("value_std") is None or float(r["value_std"]) <= 2000
                for r in rows if r.get("pollutant_code") == "PM10"
            ),
            severity="warn",
            description="PM10 value_std <= 2000 µg/m³ (plausibility).",
        ),
    ]


def silver_aerosol_suite() -> list[Expectation]:
    """``obs_aerosol`` — MODIS/VIIRS Aerosol Optical Depth (Phase 9b)."""
    return [
        expect_row_count_min(1),
        expect_not_null("aerosol_key"),
        expect_not_null("event_ts"),
        expect_not_null("aoi_id"),
        expect_not_null("stat_date"),
        expect_unique(["aerosol_key"]),
        # AOD physical range [0, 5] at 550 nm (critical — hard gate).
        expect_value_in_range("aod_550nm", 0, 5),
        expect_value_in_range("valid_fraction", 0, 1),
        expect_value_in_set("quality_flag", QUALITY_FLAGS),
        # Grain: one row per AOI / sensor / day.
        expect_unique(["aoi_id", "sensor", "stat_date"]),
        # Retrieval-completeness floor (warn) — mirrors MIN_VALID_FRACTION=0.5.
        expect_value_in_range("valid_fraction", 0.5, 1, severity="warn"),
    ]


def silver_atmos_column_suite() -> list[Expectation]:
    """``obs_atmos_column`` — TROPOMI trace-gas columns (Phase 9b)."""
    return [
        expect_row_count_min(1),
        expect_not_null("atmos_key"),
        expect_not_null("event_ts"),
        expect_not_null("aoi_id"),
        expect_not_null("gas_code"),
        expect_not_null("mean"),
        expect_unique(["atmos_key"]),
        # Enum / unit vocabulary.
        expect_value_in_set("gas_code", GAS_CODES),
        expect_value_in_set("unit_std", COLUMN_UNITS),
        expect_value_in_set("quality_flag", QUALITY_FLAGS),
        # Column density non-negative for trace gases (AER_AI may be negative).
        expect_predicate(
            "range:column_mean_non_negative",
            lambda rows: all(
                r.get("mean") is None or float(r["mean"]) >= 0
                for r in rows if r.get("gas_code") != "AER_AI"
            ),
            description="Trace-gas column mean >= 0 (AER_AI exempt).",
        ),
        expect_value_in_range("valid_pixel_fraction", 0, 1),
        # Coverage floor (warn) — mirrors MIN_VALID_PIXEL_FRACTION=0.5.
        expect_value_in_range("valid_pixel_fraction", 0.5, 1, severity="warn"),
        # Grain: one row per AOI / gas / day.
        expect_unique(["aoi_id", "gas_code", "stat_date"]),
    ]


def silver_wind_suite() -> list[Expectation]:
    """``obs_wind`` — NASA POWER daily wind at AOI representative points."""
    return [
        expect_row_count_min(1),
        expect_not_null("wind_key"),
        expect_not_null("event_ts"),
        expect_not_null("stat_date"),
        expect_not_null("aoi_id"),
        expect_not_null("parameter"),
        expect_not_null("value_std"),
        expect_not_null("unit_std"),
        expect_not_null("quality_flag"),
        expect_unique(["wind_key"]),
        expect_unique(["aoi_id", "parameter", "stat_date"]),
        expect_value_in_set("parameter", set(WIND_UNITS)),
        expect_value_in_set("unit_std", set(WIND_UNITS.values())),
        expect_value_in_set("quality_flag", QUALITY_FLAGS),
        expect_predicate(
            "consistency:wind_parameter_unit",
            lambda rows: all(
                WIND_UNITS.get(r.get("parameter")) == r.get("unit_std")
                for r in rows
            ),
            description="WS2M is m/s and WD2M is degree.",
        ),
        expect_predicate(
            "range:wind_measurement",
            lambda rows: all(
                r.get("value_std") is not None
                and 0 <= float(r["value_std"]) <= (
                    150 if r.get("parameter") == "WS2M" else 360
                )
                for r in rows
            ),
            description="WS2M in [0, 150] m/s; WD2M in [0, 360] degrees.",
        ),
    ]


# ===========================================================================
# Gold suites
# ===========================================================================


def gold_air_quality_daily_suite() -> list[Expectation]:
    """``fact_air_quality_daily`` — daily air-quality KPIs per AOI (1 row/AOI/day)."""
    return [
        expect_not_null("aoi_key"),
        expect_not_null("date_key"),
        expect_unique(["aoi_key", "date_key"]),
        # Concentrations & AQI ranges.
        expect_value_in_range("pm25_mean", 0, _MAX),
        expect_value_in_range("pm25_max", 0, _MAX),
        expect_value_in_range("pm10_mean", 0, _MAX),
        expect_value_in_range("pm10_max", 0, _MAX),
        expect_value_in_range("no2_column_mean", 0, _MAX, severity="warn"),
        expect_value_in_range("so2_column_mean", 0, _MAX, severity="warn"),
        expect_value_in_range("co_column_mean", 0, _MAX, severity="warn"),
        expect_value_in_range("o3_column_mean", 0, _MAX, severity="warn"),
        expect_value_in_range("aqi_pm25", 0, 500),
        expect_value_in_range("aqi_pm10", 0, 500),
        expect_value_in_range("station_count", 0, _MAX),
        expect_value_in_range("column_valid_fraction", 0, 1, severity="warn"),
        expect_value_in_set("aqi_band", AQI_BANDS),
        # AQI is only computed with >= 1 station; when null, no station.
        expect_predicate(
            "consistency:aqi_requires_station",
            lambda rows: all(
                (r.get("aqi_pm25") is None) or (int(r.get("station_count") or 0) >= 1)
                for r in rows
            ),
            description="aqi_pm25 populated only when station_count >= 1.",
        ),
        # Completeness (warn): AOI-days with no contributing station.
        expect_predicate(
            "completeness:station_coverage",
            lambda rows: all(int(r.get("station_count") or 0) >= 1 for r in rows),
            severity="warn",
            description="Every AOI-day has >= 1 contributing station.",
        ),
    ]


def gold_dust_event_daily_suite() -> list[Expectation]:
    """``fact_dust_event_daily`` — daily dust KPIs per AOI (1 row/AOI/day)."""
    return [
        expect_not_null("aoi_key"),
        expect_not_null("date_key"),
        expect_unique(["aoi_key", "date_key"]),
        expect_value_in_range("aod_mean", 0, 5),
        expect_value_in_range("aod_max", 0, 5),
        expect_value_in_range("corridor_aod_max", 0, 5),
        expect_value_in_range("valid_fraction", 0, 1),
        # Severity band is one of 0..4 (AOD dust-severity scheme).
        expect_value_in_set("dust_severity_band", {0, 1, 2, 3, 4}),
        expect_value_in_range("wind_speed_mean", 0, _MAX, severity="warn"),
        expect_value_in_range("valid_fraction", 0.5, 1, severity="warn"),
    ]


def gold_climate_indicator_daily_suite() -> list[Expectation]:
    """``fact_climate_indicator_daily`` — daily climate indicators per AOI."""
    return [
        expect_not_null("aoi_key"),
        expect_not_null("date_key"),
        expect_unique(["aoi_key", "date_key"]),
        # LST/SST physical bounds (°C).
        expect_value_in_range("lst_c", -90, 70),
        expect_value_in_range("sst_c", -2, 40),
        # NDWI is a normalized index.
        expect_value_in_range("ndwi_mean", -1, 1),
        # Anomalies are bounded deltas (°C).
        expect_value_in_range("lst_anomaly_c", -40, 40, severity="warn"),
        expect_value_in_range("sst_anomaly_c", -20, 20, severity="warn"),
        expect_value_in_set("lst_anomaly_band", {-1, 0, 1, 2, 3}),
    ]


def gold_vegetation_health_daily_suite() -> list[Expectation]:
    """``fact_vegetation_health_daily`` — daily vegetation-health KPIs per AOI."""
    return [
        expect_not_null("aoi_key"),
        expect_not_null("date_key"),
        expect_unique(["aoi_key", "date_key"]),
        expect_value_in_range("ndvi_mean", -1, 1),
        expect_value_in_range("ndvi_max", -1, 1),
        expect_value_in_range("evi_mean", -1, 1),
        expect_value_in_range("valid_pixel_fraction", 0, 1),
        expect_value_in_set("ndvi_health_band", {0, 1, 2, 3, 4}),
        # Cloud-free coverage floor (warn) — NDVI KPI marked estimated below 0.3.
        expect_value_in_range("valid_pixel_fraction", 0.3, 1, severity="warn"),
    ]


# ===========================================================================
# Registries
# ===========================================================================

CLIMATE_SILVER_SUITES: dict[str, Callable[[], list[Expectation]]] = {
    "obs_air_quality": silver_air_quality_suite,
    "obs_aerosol": silver_aerosol_suite,
    "obs_atmos_column": silver_atmos_column_suite,
    "obs_wind": silver_wind_suite,
}

CLIMATE_GOLD_SUITES: dict[str, Callable[[], list[Expectation]]] = {
    "fact_air_quality_daily": gold_air_quality_daily_suite,
    "fact_dust_event_daily": gold_dust_event_daily_suite,
    "fact_climate_indicator_daily": gold_climate_indicator_daily_suite,
    "fact_vegetation_health_daily": gold_vegetation_health_daily_suite,
}
