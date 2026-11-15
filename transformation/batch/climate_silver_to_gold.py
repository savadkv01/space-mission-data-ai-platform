"""Climate Silver -> Gold marts (Phase 9b).

Business-ready fact marts at **AOI-date grain**, aligned to the existing
``*_daily`` fact pattern (``kpi_wildfire_aoi_daily`` / ``kpi_flood_aoi_daily``)
and sharing ``dim_aoi`` / ``dim_date`` so fire + smoke + air quality + climate
fuse on one grain (docs/data-modeling/climate/03-gold-marts.md).

Marts produced (1 row / AOI / day):

1. ``fact_air_quality_daily``       — pollutant means/maxes, AQI bands, exceedance
2. ``fact_dust_event_daily``        — AOD, dust-index, wind context, dust-flag
3. ``fact_climate_indicator_daily`` — LST/SST anomaly, NDWI, desertification
4. ``fact_vegetation_health_daily`` — NDVI/EVI + 30-day trend, crop-stress

The KPI band/flag helpers implement the thresholds registered in
docs/data-modeling/climate/05-kpi-thresholds.md and are unit-tested directly.

Two of the marts derive their AOI membership from ``obs_index`` (which carries a
bbox, not an ``aoi_id``) via the shared point-in-polygon engine — exactly like
``gold_flood_aoi`` — because that attribution cannot be expressed in dbt SQL
(ADR-SV-01). Air-quality/dust marts consume Silver rows already AOI-tagged.
"""

from __future__ import annotations

from collections import defaultdict
from math import atan2, cos, degrees, radians, sin
from typing import Any

from transformation.batch.silver_to_gold import _bbox_centroid, _day
from transformation.geospatial.spatial_transform import attributed_aoi_keys
from transformation.timeseries.climate_indicators import (
    anomaly,
    desertification_proxy,
    linear_trend,
    same_doy_baseline,
)

# ===========================================================================
# KPI band / flag helpers (docs/data-modeling/climate/05-kpi-thresholds.md)
# ===========================================================================

#: EPA PM2.5 (µg/m³, 24-h) breakpoints: (C_low, C_high, I_low, I_high).
_PM25_BREAKPOINTS = [
    (0.0, 12.0, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 500.4, 301, 500),
]
#: EPA PM10 (µg/m³, 24-h) breakpoints.
_PM10_BREAKPOINTS = [
    (0.0, 54.0, 0, 50), (55.0, 154.0, 51, 100), (155.0, 254.0, 101, 150),
    (255.0, 354.0, 151, 200), (355.0, 424.0, 201, 300), (425.0, 604.0, 301, 500),
]

#: WHO 2021 24-h guideline values (µg/m³) driving ``exceedance_flag``.
WHO_PM25_GUIDELINE = 15.0
WHO_PM10_GUIDELINE = 45.0


def _aqi_from_breakpoints(value: float | None, breakpoints) -> int | None:
    """Piecewise-linear EPA AQI from concentration ``value`` (``None`` if absent)."""
    if value is None:
        return None
    v = float(value)
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= v <= c_high:
            aqi = (i_high - i_low) / (c_high - c_low) * (v - c_low) + i_low
            return int(round(aqi))
    return 500 if v > breakpoints[-1][1] else 0


def aqi_pm25(value: float | None) -> int | None:
    """EPA AQI index for a 24-h PM2.5 mean."""
    return _aqi_from_breakpoints(value, _PM25_BREAKPOINTS)


def aqi_pm10(value: float | None) -> int | None:
    """EPA AQI index for a 24-h PM10 mean."""
    return _aqi_from_breakpoints(value, _PM10_BREAKPOINTS)


def aqi_category(aqi: int | None) -> str | None:
    """Map a numeric AQI to its EPA category label."""
    if aqi is None:
        return None
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy (sensitive)"
    if aqi <= 200:
        return "Unhealthy"
    if aqi <= 300:
        return "Very Unhealthy"
    return "Hazardous"


# --- Region-specific AQI standards -------------------------------------------
#: The legacy EPA helpers above are labelled ``US_EPA_PRE2024`` (older PM2.5 bands,
#: no truncation; see V03). INDIA uses the CPCB National AQI (NAQI, 2014)
#: categories. NAQI bands are contiguous here (upper bound of one band = lower
#: bound of the next) so there are no concentration gaps; the open-ended
#: "Severe" band is interpolated to 500 at PM2.5 500 / PM10 600 µg/m³, a
#: platform assumption pending domain approval.
AQI_STANDARD_DEFAULT = "US_EPA_PRE2024"
AQI_STANDARD_BY_REGION = {"INDIA": "IN_CPCB_NAQI_2014"}

_NAQI_PM25 = [
    (0.0, 30.0, 0, 50), (30.0, 60.0, 50, 100), (60.0, 90.0, 100, 200),
    (90.0, 120.0, 200, 300), (120.0, 250.0, 300, 400), (250.0, 500.0, 400, 500),
]
_NAQI_PM10 = [
    (0.0, 50.0, 0, 50), (50.0, 100.0, 50, 100), (100.0, 250.0, 100, 200),
    (250.0, 350.0, 200, 300), (350.0, 430.0, 300, 400), (430.0, 600.0, 400, 500),
]


def naqi_category(aqi: int | None) -> str | None:
    """CPCB NAQI category label."""
    if aqi is None:
        return None
    for ceiling, label in ((50, "Good"), (100, "Satisfactory"), (200, "Moderate"),
                           (300, "Poor"), (400, "Very Poor")):
        if aqi <= ceiling:
            return label
    return "Severe"


def aqi_for_standard(standard: str, pm25_mean: float | None,
                     pm10_mean: float | None) -> tuple[int | None, int | None, str | None]:
    """``(aqi_pm25, aqi_pm10, band)`` under ``standard``; band uses the worst sub-index."""
    if standard == "IN_CPCB_NAQI_2014":
        a25 = _aqi_from_breakpoints(pm25_mean, _NAQI_PM25)
        a10 = _aqi_from_breakpoints(pm10_mean, _NAQI_PM10)
        overall = max([a for a in (a25, a10) if a is not None], default=None)
        return a25, a10, naqi_category(overall)
    a25, a10 = aqi_pm25(pm25_mean), aqi_pm10(pm10_mean)
    overall = max([a for a in (a25, a10) if a is not None], default=None)
    return a25, a10, aqi_category(overall)


def air_quality_exceedance(pm25_mean: float | None, pm10_mean: float | None) -> bool:
    """``True`` when a daily pollutant mean exceeds its WHO 2021 guideline."""
    return bool(
        (pm25_mean is not None and pm25_mean > WHO_PM25_GUIDELINE)
        or (pm10_mean is not None and pm10_mean > WHO_PM10_GUIDELINE)
    )


#: AOD dust-severity bands (unitless, 550 nm): (band, label, low, high).
_DUST_BANDS = [
    (0, "Clear", 0.0, 0.2), (1, "Hazy", 0.2, 0.5), (2, "Dusty", 0.5, 1.0),
    (3, "Heavy dust", 1.0, 2.0), (4, "Severe", 2.0, 5.0),
]
DUST_AOD_THRESHOLD = 0.5
DUST_UV_AI_THRESHOLD = 1.0


def dust_severity_band(aod: float | None) -> int | None:
    """AOD load band 0..4 (aerosol load of any type; dust only if ``dust_flag``)."""
    if aod is None:
        return None
    v = float(aod)
    for band, _label, low, high in _DUST_BANDS:
        if low <= v < high:
            return band
    return 4 if v >= 5.0 else 0


#: MAIAC aerosol-model share (of QA-passing pixels) that makes a type dominant.
AEROSOL_TYPE_DOMINANT_SHARE = 0.5


def aerosol_type(smoke_fraction: float | None, dust_fraction: float | None) -> str | None:
    """Dominant MAIAC aerosol model: ``dust`` / ``smoke`` / ``mixed`` / ``background``.

    ``None`` when no aerosol-model information exists (legacy or non-MAIAC AOD).
    ``mixed`` = smoke and dust together dominate but neither alone does.
    """
    if smoke_fraction is None and dust_fraction is None:
        return None
    smoke, dust = smoke_fraction or 0.0, dust_fraction or 0.0
    if dust >= AEROSOL_TYPE_DOMINANT_SHARE:
        return "dust"
    if smoke >= AEROSOL_TYPE_DOMINANT_SHARE:
        return "smoke"
    if smoke + dust >= AEROSOL_TYPE_DOMINANT_SHARE:
        return "mixed"
    return "background"


def dust_flag(aod_mean: float | None, uv_ai_mean: float | None,
              dust_fraction: float | None = None) -> bool:
    """Dust event: elevated AOD **and** dust evidence.

    With MAIAC aerosol-model information the evidence is a dust-model share of
    at least ``AEROSOL_TYPE_DOMINANT_SHARE``; this keeps crop-burning smoke (which
    also raises the UV aerosol index) from reading as dust (L5 / D-07). Without
    it, the UV aerosol index must corroborate (legacy rule).
    """
    if aod_mean is None or aod_mean < DUST_AOD_THRESHOLD:
        return False
    if dust_fraction is not None:
        return dust_fraction >= AEROSOL_TYPE_DOMINANT_SHARE
    return uv_ai_mean is not None and uv_ai_mean >= DUST_UV_AI_THRESHOLD


#: Transport: a same-region source AOI counts as upwind when its bearing from
#: the receiving AOI is within this many degrees of the wind's from-direction.
UPWIND_HALF_ANGLE_DEG = 45.0


def initial_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle initial bearing (0 = north, clockwise) from point 1 to point 2."""
    p1, p2 = radians(lat1), radians(lat2)
    dl = radians(lon2 - lon1)
    x = sin(dl) * cos(p2)
    y = cos(p1) * sin(p2) - sin(p1) * cos(p2) * cos(dl)
    return (degrees(atan2(x, y)) + 360.0) % 360.0


def is_upwind(target: tuple[float, float], source: tuple[float, float],
              wind_from_deg: float) -> bool:
    """``True`` when ``source`` lies within the upwind sector of ``target``.

    ``target`` / ``source`` are ``(lat, lon)``; ``wind_from_deg`` is the
    meteorological direction the wind blows *from* (NASA POWER WD2M).
    """
    bearing = initial_bearing_deg(target[0], target[1], source[0], source[1])
    diff = abs((bearing - wind_from_deg + 180.0) % 360.0 - 180.0)
    return diff <= UPWIND_HALF_ANGLE_DEG


#: LST anomaly bands (°C above same-DOY baseline): (band, label, low, high).
LST_WARMING_THRESHOLD = 3.0
SST_WARMING_THRESHOLD = 1.5


def lst_anomaly_band(anomaly_c: float | None) -> int | None:
    """Warming band from an LST anomaly (°C): -1 cooler .. 3 extreme."""
    if anomaly_c is None:
        return None
    v = float(anomaly_c)
    if v < -1.0:
        return -1
    if v < 1.0:
        return 0
    if v < 3.0:
        return 1
    if v < 5.0:
        return 2
    return 3


def warming_flag(lst_anomaly_c: float | None, sst_anomaly_c: float | None) -> bool:
    """``True`` when the LST or coastal SST anomaly clears its warming threshold."""
    return bool(
        (lst_anomaly_c is not None and lst_anomaly_c >= LST_WARMING_THRESHOLD)
        or (sst_anomaly_c is not None and sst_anomaly_c >= SST_WARMING_THRESHOLD)
    )


DESERTIFICATION_THRESHOLD = 0.5


def desertification_flag(proxy: float | None) -> bool:
    """``True`` when the desertification proxy clears its threshold."""
    return bool(proxy is not None and proxy >= DESERTIFICATION_THRESHOLD)


#: NDVI health bands (unitless): (band, label, low, high).
def ndvi_health_band(ndvi: float | None) -> int | None:
    """Vegetation-health band 0..4 from an NDVI value."""
    if ndvi is None:
        return None
    v = float(ndvi)
    if v < 0.1:
        return 0
    if v < 0.3:
        return 1
    if v < 0.5:
        return 2
    if v < 0.7:
        return 3
    return 4


def crop_stress_flag(ndvi_mean: float | None, ndvi_trend_30d: float | None,
                     cropland: bool = True) -> bool | None:
    """``True`` when NDVI is low **and** declining (crop / vegetation stress).

    ``None`` (not evaluated) for an AOI that is not cropland: low, declining
    NDVI over sea, desert or a city is not crop stress (D-08).
    """
    if not cropland:
        return None
    return bool(
        ndvi_mean is not None and ndvi_mean < 0.3
        and ndvi_trend_30d is not None and ndvi_trend_30d < 0
    )


# ===========================================================================
# Shared aggregation helpers
# ===========================================================================

def _mean(values: list[float]) -> float | None:
    vals = [float(v) for v in values if v is not None]
    return round(sum(vals) / len(vals), 6) if vals else None


def _attribute_index(index_rows: list[dict[str, Any]], aois: list[dict[str, Any]],
                     index_names: set[str]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Group ``obs_index`` rows by (aoi_key, day) via bbox-centroid point-in-polygon.

    Mirrors ``gold_flood_aoi``: an index bucket's bbox centroid is attributed to
    every AOI whose footprint contains it, so climate/vegetation marts land at
    the same AOI-date grain as the EO facts.
    """
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in index_rows:
        if str(r.get("index_name", "")).upper() not in index_names:
            continue
        day = _day(r.get("event_ts") or r.get("stat_date"))
        lat, lon = _bbox_centroid(r.get("bbox"))
        if not day or lat is None:
            continue
        for aoi_key in attributed_aoi_keys(lat, lon, aois):
            groups[(aoi_key, day)].append(r)
    return groups


# ===========================================================================
# 1. fact_air_quality_daily
# ===========================================================================

def gold_air_quality_daily(silver_air_quality: list[dict[str, Any]],
                           silver_atmos_column: list[dict[str, Any]] | None = None,
                           aoi_regions: dict[str, str | None] | None = None,
                           ) -> list[dict[str, Any]]:
    """Daily air-quality KPIs per AOI (``fact_air_quality_daily``).

    Surface PM/pollutants come from AOI-tagged OpenAQ rows; the TROPOMI column
    means are joined in on ``aoi_id`` + ``stat_date``. AQI is computed only where
    at least one station contributed (``station_count`` >= 1), under the AOI
    region's standard (``aqi_standard``; ``AQI_STANDARD_BY_REGION``).
    """
    aoi_regions = aoi_regions or {}
    surface: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in silver_air_quality:
        aoi = r.get("aoi_id")
        day = r.get("stat_date") or _day(r.get("event_ts"))
        if aoi and day:
            surface[(aoi, day)].append(r)

    columns: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in silver_atmos_column or []:
        aoi = r.get("aoi_id")
        day = r.get("stat_date") or _day(r.get("event_ts"))
        if aoi and day:
            columns[(aoi, day)].append(r)

    out = []
    for key in sorted(set(surface) | set(columns)):
        aoi, day = key
        rows = [
            row for row in surface.get(key, [])
            if row.get("quality_flag") == "valid"
        ]
        pm25 = [r["value_std"] for r in rows
                if r.get("pollutant_code") == "PM25" and r.get("value_std") is not None]
        pm10 = [r["value_std"] for r in rows
                if r.get("pollutant_code") == "PM10" and r.get("value_std") is not None]
        stations = {
            r.get("location_id") for r in rows
            if r.get("location_id")
            and r.get("pollutant_code") in {"PM25", "PM10"}
            and r.get("value_std") is not None
        }

        col_rows = columns.get(key, [])
        gas_means = defaultdict(list)
        for c in col_rows:
            if c.get("mean") is not None and c.get("quality_flag") != "low_coverage":
                gas_means[c.get("gas_code")].append(float(c["mean"]))
        valid_fracs = [c["valid_pixel_fraction"] for c in col_rows
                       if c.get("valid_pixel_fraction") is not None]

        pm25_mean = _mean(pm25)
        pm10_mean = _mean(pm10)
        station_count = len(stations)
        standard = AQI_STANDARD_BY_REGION.get(aoi_regions.get(aoi), AQI_STANDARD_DEFAULT)
        if station_count >= 1:
            aqi25, aqi10, band = aqi_for_standard(standard, pm25_mean, pm10_mean)
        else:
            aqi25 = aqi10 = band = None

        out.append({
            "aoi_key": aoi,
            "date_key": day,
            "pm25_mean": pm25_mean,
            "pm25_max": round(max(pm25), 6) if pm25 else None,
            "pm10_mean": pm10_mean,
            "pm10_max": round(max(pm10), 6) if pm10 else None,
            "no2_column_mean": _mean(gas_means.get("NO2", [])),
            "so2_column_mean": _mean(gas_means.get("SO2", [])),
            "co_column_mean": _mean(gas_means.get("CO", [])),
            "o3_column_mean": _mean(gas_means.get("O3", [])),
            "station_count": station_count,
            "column_valid_fraction": _mean(valid_fracs),
            "aqi_pm25": aqi25,
            "aqi_pm10": aqi10,
            "aqi_band": band,
            "aqi_standard": standard,
            "exceedance_flag": air_quality_exceedance(pm25_mean, pm10_mean),
        })
    return out


# ===========================================================================
# 2. fact_dust_event_daily
# ===========================================================================

def gold_dust_event_daily(silver_aerosol: list[dict[str, Any]],
                          silver_atmos_column: list[dict[str, Any]] | None = None,
                          wind_by_aoi_day: dict[tuple[str, str], dict[str, float]] | None = None,
                          aoi_regions: dict[str, str | None] | None = None,
                          aoi_centroids: dict[str, tuple[float, float]] | None = None,
                          ) -> list[dict[str, Any]]:
    """Daily dust KPIs per AOI (``fact_dust_event_daily``).

    AOD comes from ``obs_aerosol``; the UV aerosol index is taken from the aerosol
    row when present, otherwise denormalized from the TROPOMI ``AER_AI`` column.
    MAIAC aerosol-model shares give ``smoke_fraction`` / ``dust_fraction`` and the
    dominant ``aerosol_type``.

    ``corridor_aod_max`` is the strongest AOD over the *upwind* AOIs of the same
    analysis region on the same day (D-06): a source AOI counts only if its
    bearing from this AOI's centroid is within ``UPWIND_HALF_ANGLE_DEG`` of the
    NASA POWER wind direction. Without a wind direction or centroids nothing is
    upwind, so the corridor is ``None`` and transport is not asserted.
    """
    wind_by_aoi_day = wind_by_aoi_day or {}
    aoi_regions = aoi_regions or {}
    aoi_centroids = aoi_centroids or {}

    aer: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in silver_aerosol:
        aoi = r.get("aoi_id")
        day = r.get("stat_date") or _day(r.get("event_ts"))
        if aoi and day:
            aer[(aoi, day)].append(r)

    aer_ai: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in silver_atmos_column or []:
        if r.get("gas_code") == "AER_AI" and r.get("mean") is not None:
            aoi = r.get("aoi_id")
            day = r.get("stat_date") or _day(r.get("event_ts"))
            if aoi and day:
                aer_ai[(aoi, day)].append(float(r["mean"]))

    # Per-day max AOD per AOI (candidate upwind sources).
    day_aod_by_aoi: dict[str, dict[str, float]] = defaultdict(dict)
    for (aoi, day), rows in aer.items():
        aods = [r["aod_550nm"] for r in rows if r.get("aod_550nm") is not None]
        if aods:
            day_aod_by_aoi[day][aoi] = max(aods)

    out = []
    for (aoi, day), rows in sorted(aer.items()):
        aods = [r["aod_550nm"] for r in rows if r.get("aod_550nm") is not None]
        aod_mean = _mean(aods)
        uv_from_aer = [r["uv_aerosol_index"] for r in rows
                       if r.get("uv_aerosol_index") is not None]
        uv_mean = _mean(uv_from_aer) if uv_from_aer else _mean(aer_ai.get((aoi, day), []))
        valid = [r["valid_fraction"] for r in rows if r.get("valid_fraction") is not None]
        smoke = _mean([r.get("smoke_fraction") for r in rows])
        dust = _mean([r.get("dust_fraction") for r in rows])

        wind = wind_by_aoi_day.get((aoi, day), {})
        wind_speed = wind.get("wind_speed_mean")
        wind_dir = wind.get("wind_dir_dominant")
        region = aoi_regions.get(aoi)
        target = aoi_centroids.get(aoi)
        upwind = []
        if wind_dir is not None and target is not None:
            for source, value in day_aod_by_aoi.get(day, {}).items():
                centre = aoi_centroids.get(source)
                if (source != aoi and centre is not None
                        and aoi_regions.get(source) == region
                        and is_upwind(target, centre, float(wind_dir))):
                    upwind.append(value)
        corridor = round(max(upwind), 6) if upwind else None
        transport = bool(corridor is not None and corridor >= DUST_AOD_THRESHOLD
                         and wind_speed is not None and wind_speed > 0)

        out.append({
            "aoi_key": aoi,
            "date_key": day,
            "aod_mean": aod_mean,
            "aod_max": round(max(aods), 6) if aods else None,
            "uv_aerosol_index_mean": uv_mean,
            "wind_speed_mean": wind_speed,
            "wind_dir_dominant": wind_dir,
            "corridor_aod_max": corridor,
            "valid_fraction": _mean(valid),
            "smoke_fraction": smoke,
            "dust_fraction": dust,
            "aerosol_type": aerosol_type(smoke, dust),
            "dust_severity_band": dust_severity_band(aod_mean),
            "dust_flag": dust_flag(aod_mean, uv_mean, dust),
            "transport_flag": transport,
        })
    return out


# ===========================================================================
# 3. fact_climate_indicator_daily
# ===========================================================================

def _daily_series(groups: dict[tuple[str, str], list[dict[str, Any]]],
                  index_name: str) -> dict[str, list[tuple[str, float]]]:
    """Per-AOI ordered ``(day, mean)`` series for one index (for trend/anomaly)."""
    series: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (aoi, day), rows in groups.items():
        means = [float(r["mean"]) for r in rows
                 if str(r.get("index_name", "")).upper() == index_name
                 and r.get("mean") is not None]
        if means:
            series[aoi].append((day, sum(means) / len(means)))
    for aoi in series:
        series[aoi].sort(key=lambda t: t[0])
    return series


def gold_climate_indicator_daily(silver_index: list[dict[str, Any]],
                                 aois: list[dict[str, Any]],
                                 ) -> list[dict[str, Any]]:
    """Daily climate indicators per AOI (``fact_climate_indicator_daily``).

    Derived entirely from already-ingested ``obs_index`` statistics (NDWI, plus
    LST / SST / NDVI where present — zero new connectors). LST/SST anomalies use
    the same-day-of-year baseline; the desertification proxy composes the NDVI
    trend with the LST anomaly.
    """
    groups = _attribute_index(silver_index, aois,
                              {"NDVI", "NDWI", "LST", "SST", "EVI"})

    # Seasonal baselines (same day-of-year) per AOI for LST/SST anomalies.
    lst_points: dict[str, list[dict[str, Any]]] = defaultdict(list)
    sst_points: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (aoi, _day_key), rows in groups.items():
        for r in rows:
            name = str(r.get("index_name", "")).upper()
            if name == "LST" and r.get("mean") is not None:
                lst_points[aoi].append({"event_ts": r.get("event_ts"), "v": float(r["mean"])})
            elif name == "SST" and r.get("mean") is not None:
                sst_points[aoi].append({"event_ts": r.get("event_ts"), "v": float(r["mean"])})
    lst_baseline = {aoi: same_doy_baseline(pts, "v") for aoi, pts in lst_points.items()}
    sst_baseline = {aoi: same_doy_baseline(pts, "v") for aoi, pts in sst_points.items()}

    ndvi_series = _daily_series(groups, "NDVI")

    def _ndvi_trend(aoi: str, day: str) -> float | None:
        pts = [v for d, v in ndvi_series.get(aoi, []) if d <= day][-30:]
        return linear_trend(pts) if len(pts) >= 2 else None

    from transformation.timeseries.climate_indicators import day_of_year

    out = []
    for (aoi, day), rows in sorted(groups.items()):
        by_index: dict[str, list[float]] = defaultdict(list)
        for r in rows:
            if r.get("mean") is not None:
                by_index[str(r.get("index_name", "")).upper()].append(float(r["mean"]))

        lst_c = _mean(by_index.get("LST", []))
        sst_c = _mean(by_index.get("SST", []))
        doy = day_of_year(day)
        lst_anom = anomaly(lst_c, lst_baseline.get(aoi, {}).get(doy)) if doy else None
        sst_anom = anomaly(sst_c, sst_baseline.get(aoi, {}).get(doy)) if doy else None
        ndvi_trend = _ndvi_trend(aoi, day)
        proxy = desertification_proxy(ndvi_trend, lst_anom)

        out.append({
            "aoi_key": aoi,
            "date_key": day,
            "lst_c": lst_c,
            "lst_anomaly_c": lst_anom,
            "sst_c": sst_c,
            "sst_anomaly_c": sst_anom,
            "ndwi_mean": _mean(by_index.get("NDWI", [])),
            "tree_cover_loss_ha": None,  # GFW annual allocation — no source ingested
            "desertification_proxy": proxy,
            "lst_anomaly_band": lst_anomaly_band(lst_anom),
            "warming_flag": warming_flag(lst_anom, sst_anom),
            "desertification_flag": desertification_flag(proxy),
        })
    return out


# ===========================================================================
# 4. fact_vegetation_health_daily
# ===========================================================================

def gold_vegetation_health_daily(silver_index: list[dict[str, Any]],
                                 aois: list[dict[str, Any]],
                                 ) -> list[dict[str, Any]]:
    """Daily vegetation-health KPIs per AOI (``fact_vegetation_health_daily``).

    Reuses the ``obs_index`` NDVI/EVI Silver mart (Sentinel-2 / MODIS). The
    30-day NDVI slope is the OLS trend over the trailing daily NDVI means for the
    AOI; ``crop_stress_flag`` fires when NDVI is both low and declining, and is
    evaluated only on cropland AOIs (``crop_stress_applicable``; seed ``cropland``).
    """
    groups = _attribute_index(silver_index, aois, {"NDVI", "EVI"})
    ndvi_series = _daily_series(groups, "NDVI")
    cropland = {a.get("aoi_key"): a.get("cropland") is True for a in aois}

    out = []
    for (aoi, day), rows in sorted(groups.items()):
        ndvi = [float(r["mean"]) for r in rows
                if str(r.get("index_name", "")).upper() == "NDVI" and r.get("mean") is not None]
        evi = [float(r["mean"]) for r in rows
               if str(r.get("index_name", "")).upper() == "EVI" and r.get("mean") is not None]
        valid = [float(r["valid_pixel_fraction"]) for r in rows
                 if r.get("valid_pixel_fraction") is not None]
        pts = [v for d, v in ndvi_series.get(aoi, []) if d <= day][-30:]
        trend = linear_trend(pts) if len(pts) >= 2 else None
        ndvi_mean = _mean(ndvi)

        out.append({
            "aoi_key": aoi,
            "date_key": day,
            "ndvi_mean": ndvi_mean,
            "ndvi_max": round(max(ndvi), 6) if ndvi else None,
            "evi_mean": _mean(evi),
            "ndvi_trend_30d": trend,
            "valid_pixel_fraction": _mean(valid),
            "ndvi_health_band": ndvi_health_band(ndvi_mean),
            "crop_stress_applicable": cropland.get(aoi, False),
            "crop_stress_flag": crop_stress_flag(ndvi_mean, trend, cropland.get(aoi, False)),
        })
    return out
