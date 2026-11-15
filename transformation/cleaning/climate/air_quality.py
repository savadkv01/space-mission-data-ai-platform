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
        "qa_reason": None,
        "source": record.get("_source") or "OPENAQ",
        "_ingest_id": record.get("_ingest_id"),
        "_batch_id": record.get("_batch_id"),
    }
    return CleanResult.keep(out)


# --- Sensor plausibility (D-09) ---------------------------------------------
#
# Per-reading cleaning cannot see a stuck sensor or an isolated spike; both need
# the station's time series. These rules run on the deduplicated Silver rows and
# downgrade readings to ``suspect`` (kept, but excluded from Gold aggregates,
# which use ``quality_flag == "valid"`` only).

#: Upper plausibility bound per pollutant (µg/m³). Real Delhi peaks stay below.
PLAUSIBLE_MAX = {"PM25": 1000.0, "PM10": 2000.0}
#: Identical consecutive readings that mark a stuck (flat-lined) sensor:
#: 2 h at the common 15-minute cadence, 8 h for hourly sensors.
FLATLINE_MIN_RUN = 8
#: Near instrument full scale (BAM monitors read 0-1000 µg/m³) a short identical
#: plateau is a saturation artefact, not a measurement (Delhi station 5598:
#: 25 -> 992 x4 -> 82 within an hour).
SATURATION_LEVEL = 900.0
SATURATION_MIN_RUN = 3
#: Rise from the previous reading that ambient PM cannot make in one interval
#: (Delhi station 5586: 0.06 -> 1000 -> 556 µg/m³ in 15-minute steps).
JUMP_MIN = 500.0
#: An isolated reading is a spike when it exceeds both neighbours by this
#: factor *and* by this absolute margin (µg/m³).
SPIKE_RATIO = 3.0
SPIKE_MIN_JUMP = 250.0


def flag_sensor_anomalies(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mark out-of-range, flat-lined, saturated, jump and spike readings ``suspect``.

    Rows are grouped per (location, pollutant) and ordered by event time.
    ``qa_reason`` records the first rule that fired. Smooth rises to very high
    values (real severe-smog nights) are kept. Returns ``rows``.
    """
    series: dict[tuple[Any, Any], list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("value_std") is None or row.get("quality_flag") != "valid":
            continue
        series.setdefault((row.get("location_id"), row.get("pollutant_code")), []).append(row)

    def _suspect(row: dict[str, Any], reason: str) -> None:
        if row.get("quality_flag") == "valid":
            row["quality_flag"] = "suspect"
            row["qa_reason"] = reason

    for (_, pollutant), readings in series.items():
        readings.sort(key=lambda r: str(r.get("event_ts") or ""))
        ceiling = PLAUSIBLE_MAX.get(str(pollutant))
        if ceiling is not None:
            for r in readings:
                if r["value_std"] > ceiling:
                    _suspect(r, "out_of_range")

        start = 0
        for i in range(1, len(readings) + 1):
            if i < len(readings) and readings[i]["value_std"] == readings[start]["value_std"]:
                continue
            run, level = i - start, readings[start]["value_std"]
            if run >= FLATLINE_MIN_RUN and level > 0:
                for r in readings[start:i]:
                    _suspect(r, "flat_line")
            elif run >= SATURATION_MIN_RUN and level >= SATURATION_LEVEL:
                for r in readings[start:i]:
                    _suspect(r, "saturation")
            start = i

        for i in range(1, len(readings) - 1):
            prev_v = readings[i - 1]["value_std"]
            cur_v = readings[i]["value_std"]
            next_v = readings[i + 1]["value_std"]
            neighbour = max(prev_v, next_v)
            if cur_v > SPIKE_RATIO * neighbour and cur_v - neighbour > SPIKE_MIN_JUMP:
                _suspect(readings[i], "spike")

        for i in range(1, len(readings)):
            if readings[i]["value_std"] - readings[i - 1]["value_std"] >= JUMP_MIN:
                _suspect(readings[i], "jump")
    return rows
