"""NASA POWER daily wind measurement cleaner."""

from __future__ import annotations

from math import isfinite
from typing import Any

from transformation.cleaning.cleaning_rules import (
    CleanResult,
    normalize_timestamp,
    stable_key,
    to_float,
)


def _event_timestamp(record: dict[str, Any]) -> str | None:
    value = record.get("_event_ts") or record.get("date")
    if isinstance(value, str) and len(value) == 8 and value.isdigit():
        value = f"{value[:4]}-{value[4:6]}-{value[6:]}T00:00:00Z"
    return normalize_timestamp(value)


def clean_power_wind(record: dict[str, Any]) -> CleanResult:
    """Conform a NASA POWER WS2M or WD2M daily value to a Silver measurement."""
    parameter = str(record.get("parameter") or "").upper()
    value = to_float(record.get("value"))
    event_ts = _event_timestamp(record)

    reasons: list[str] = []
    if parameter not in {"WS2M", "WD2M"}:
        reasons.append("unknown:wind_parameter")
    if not record.get("aoi_id"):
        reasons.append("null:aoi_id")
    if event_ts is None:
        reasons.append("timestamp:unparseable")
    if value is None or not isfinite(value):
        reasons.append("value:non_finite")
    elif parameter == "WS2M" and not 0 <= value <= 150:
        reasons.append("range:wind_speed")
    elif parameter == "WD2M" and not 0 <= value <= 360:
        reasons.append("range:wind_direction")
    if reasons:
        return CleanResult.reject(reasons)

    stat_date = event_ts[:10]
    return CleanResult.keep({
        "wind_key": stable_key(record["aoi_id"], stat_date, parameter),
        "event_ts": event_ts,
        "stat_date": stat_date,
        "aoi_id": record["aoi_id"],
        "parameter": parameter,
        "value_std": round(value, 6),
        "unit_std": "m/s" if parameter == "WS2M" else "degree",
        "latitude": to_float(record.get("latitude")),
        "longitude": to_float(record.get("longitude")),
        "quality_flag": "valid",
        "source": record.get("_source") or "POWER",
        "_ingest_id": record.get("_ingest_id"),
        "_batch_id": record.get("_batch_id"),
    })
