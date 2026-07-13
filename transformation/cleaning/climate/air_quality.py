"""``obs_air_quality`` cleaner — OpenAQ surface pollutant readings (Phase 9b).

Conforms one OpenAQ v3 measurement (unwrapped from its Bronze envelope) to the
Silver ``obs_air_quality`` schema: canonical pollutant code, unit-standardized
value, WGS84 coordinates + ``geo_key``, and a ``quality_flag``. Station -> AOI
tagging (point-in-polygon) is applied by the Silver driver in
:mod:`transformation.batch.climate_bronze_to_silver`, which has the AOI list.

Grain: 1 row / station / pollutant / reading. Natural key hashes
(location_id, sensor_id, pollutant_code, event_ts).
"""

from __future__ import annotations

from typing import Any

from transformation.cleaning.cleaning_rules import (
    CleanResult,
    normalize_timestamp,
    require_fields,
    stable_key,
    to_float,
)
from transformation.cleaning.climate.units import (
    canonical_pollutant_code,
    standardize_pollutant_value,
)
from transformation.geospatial.spatial_transform import (
    clamp_lat,
    geo_key,
    normalize_lon,
)


def _coords(record: dict[str, Any]) -> tuple[float | None, float | None]:
    """Return ``(lat, lon)`` from the v3 ``coordinates`` block or flat fields."""
    coords = record.get("coordinates")
    if isinstance(coords, dict):
        return to_float(coords.get("latitude")), to_float(coords.get("longitude"))
    return to_float(record.get("latitude")), to_float(record.get("longitude"))


def _event_ts(record: dict[str, Any]) -> str | None:
    """Tolerant timestamp extraction across OpenAQ v2/v3 shapes + provenance."""
    for key in ("date", "datetime", "period"):
        node = record.get(key)
        if isinstance(node, dict):
            ts = node.get("utc") or node.get("datetime_utc") or node.get("datetimeFrom")
            if isinstance(ts, dict):
                ts = ts.get("utc")
            if ts:
                return normalize_timestamp(ts)
    flat = record.get("datetime_utc") or record.get("datetime") or record.get("_event_ts")
    return normalize_timestamp(flat)


def _location_id(record: dict[str, Any]) -> Any:
    return (
        record.get("locationId")
        or record.get("location_id")
        or record.get("locationsId")
        or record.get("location")
    )


def _sensor_id(record: dict[str, Any]) -> Any:
    return record.get("sensorsId") or record.get("sensorId") or record.get("sensor_id")


def _raw_unit(record: dict[str, Any], parameter: Any) -> Any:
    unit = record.get("unit") or record.get("units")
    if unit is None and isinstance(parameter, dict):
        unit = parameter.get("units") or parameter.get("unit")
    return unit


def clean_air_quality(record: dict[str, Any]) -> CleanResult:
    """Conform an OpenAQ measurement to the Silver ``obs_air_quality`` schema."""
    parameter = record.get("parameter")
    param_name = parameter.get("name") if isinstance(parameter, dict) else parameter
    pollutant_code = canonical_pollutant_code(param_name)
    lat, lon = _coords(record)
    ts = _event_ts(record)

    reasons: list[str] = []
    reasons += require_fields(record, ["value"])
    if pollutant_code is None:
        reasons.append("unknown:pollutant")
    if ts is None:
        reasons.append("timestamp:unparseable")
    if lat is None or lon is None:
        reasons.append("null:coordinates")
    elif not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        reasons.append("range:coordinates")
    value_raw = to_float(record.get("value"))
    if value_raw is not None and value_raw < 0:
        reasons.append("range:value")
    if reasons:
        return CleanResult.reject(reasons)

    lat = clamp_lat(float(lat))
    lon = normalize_lon(float(lon))
    unit_raw = _raw_unit(record, parameter)
    value_std, quality_flag = standardize_pollutant_value(pollutant_code, value_raw, unit_raw)
    location_id = _location_id(record)
    sensor_id = _sensor_id(record)

    out = {
        "air_quality_key": stable_key(location_id, sensor_id, pollutant_code, ts),
        "event_ts": ts,
        "stat_date": ts[:10],
        "location_id": str(location_id) if location_id is not None else None,
        "pollutant_code": pollutant_code,
        "value_std": value_std,
        "value_raw": value_raw,
        "unit_raw": str(unit_raw) if unit_raw is not None else None,
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        "geo_key": geo_key(lat, lon),
        # AOI membership is resolved by the driver (point-in-polygon). The
        # Bronze-stamped request AOI is a fallback when no polygon matches.
        "aoi_id": record.get("aoi_id"),
        "quality_flag": quality_flag,
        "source": record.get("_source") or "OPENAQ",
        "_ingest_id": record.get("_ingest_id"),
        "_batch_id": record.get("_batch_id"),
    }
    return CleanResult.keep(out)
