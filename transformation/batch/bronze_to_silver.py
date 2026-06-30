"""Bronze -> Silver transforms (Task 3).

Each ``silver_*`` function takes a list of *unwrapped* Bronze records (source
payload + provenance columns, see ``common/io.unwrap_bronze``) and returns a
:class:`SilverResult` with conformed rows and quarantined rows.

Silver guarantees, per the Phase 6 contract (docs/data-modeling/03-silver-layer.md):
- canonical UTC ISO-8601 timestamps
- required natural keys present
- ranges enforced; geospatial normalized to WGS84 + grid key
- deduplicated by natural key, keeping the latest event

The same rule functions are wrapped as Spark UDFs in :func:`run_spark` so the
cluster job and the offline path share one definition of "clean".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from transformation.cleaning.cleaning_rules import (
    CleanResult,
    deduplicate,
    in_range,
    normalize_timestamp,
    require_fields,
    to_float,
)
from transformation.geospatial.spatial_transform import normalize_position


@dataclass
class SilverResult:
    entity: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    quarantine: list[dict[str, Any]] = field(default_factory=list)

    @property
    def rows_in(self) -> int:
        return len(self.rows) + len(self.quarantine)


def _quarantine(record: dict[str, Any], reasons: list[str], entity: str) -> dict[str, Any]:
    return {"_entity": entity, "_reasons": reasons, "payload": record}


# --- Satellite telemetry ----------------------------------------------------

def clean_telemetry(record: dict[str, Any]) -> CleanResult:
    """Conform a single telemetry record to the Silver telemetry schema.

    Flattens nested sensor readings into typed columns and lifts the embedded
    health/anomaly label for downstream features.
    """
    reasons = require_fields(record, ["timestamp", "satellite_id"])
    ts = normalize_timestamp(record.get("timestamp"))
    if ts is None:
        reasons.append("timestamp:unparseable")
    if reasons:
        return CleanResult.reject(reasons)

    payload = record.get("payload") or {}
    metadata = record.get("metadata") or {}
    out: dict[str, Any] = {
        "event_ts": ts,
        "satellite_id": record["satellite_id"],
        "sensor_type": record.get("sensor_type", "unknown"),
        "health": metadata.get("health", "UNKNOWN"),
        "label_anomaly": bool(metadata.get("label_anomaly", False)),
        "_ingest_id": record.get("_ingest_id"),
        "_batch_id": record.get("_batch_id"),
    }
    # Flatten sensor readings: battery_voltage -> battery_voltage_value/_status.
    anomaly_sensors = []
    for sensor, reading in payload.items():
        if not isinstance(reading, dict):
            continue
        out[f"{sensor}_value"] = to_float(reading.get("value"))
        out[f"{sensor}_unit"] = reading.get("unit")
        status = reading.get("status", "NOMINAL")
        out[f"{sensor}_status"] = status
        if status == "ANOMALY":
            anomaly_sensors.append(sensor)
    out["anomaly_sensor_count"] = len(anomaly_sensors)
    out["anomaly_sensors"] = anomaly_sensors
    return CleanResult.keep(out)


def silver_telemetry(records: list[dict[str, Any]]) -> SilverResult:
    return _apply(records, clean_telemetry, entity="silver_telemetry",
                  key_fields=["satellite_id", "event_ts"])


# --- Orbit position ---------------------------------------------------------

def clean_orbit(record: dict[str, Any]) -> CleanResult:
    reasons = require_fields(record, ["timestamp", "satellite_id", "latitude", "longitude"])
    ts = normalize_timestamp(record.get("timestamp"))
    if ts is None:
        reasons.append("timestamp:unparseable")
    if not in_range(record.get("latitude"), -90, 90):
        reasons.append("range:latitude")
    if not in_range(record.get("longitude"), -180, 180):
        reasons.append("range:longitude")
    if record.get("altitude_km") is not None and not in_range(record.get("altitude_km"), 0, 50000):
        reasons.append("range:altitude_km")
    if reasons:
        return CleanResult.reject(reasons)

    base = normalize_position({
        "event_ts": ts,
        "satellite_id": record["satellite_id"],
        "latitude": to_float(record["latitude"]),
        "longitude": to_float(record["longitude"]),
        "altitude_km": to_float(record.get("altitude_km")),
        "propagator": record.get("propagator", "unknown"),
        "_ingest_id": record.get("_ingest_id"),
        "_batch_id": record.get("_batch_id"),
    })
    return CleanResult.keep(base)


def silver_orbit(records: list[dict[str, Any]]) -> SilverResult:
    return _apply(records, clean_orbit, entity="silver_orbit",
                  key_fields=["satellite_id", "event_ts"])


# --- Space weather ----------------------------------------------------------

def clean_space_weather(record: dict[str, Any]) -> CleanResult:
    reasons = require_fields(record, ["timestamp", "kp_index"])
    ts = normalize_timestamp(record.get("timestamp"))
    if ts is None:
        reasons.append("timestamp:unparseable")
    if not in_range(record.get("kp_index"), 0, 9):
        reasons.append("range:kp_index")
    if reasons:
        return CleanResult.reject(reasons)

    kp = to_float(record["kp_index"]) or 0.0
    out = {
        "event_ts": ts,
        "event_type": record.get("event_type", "space_weather"),
        "kp_index": kp,
        "flare_class": str(record.get("flare_class", "A0")).upper(),
        "flare_letter": str(record.get("flare_class", "A0")).upper()[:1],
        "geomagnetic_storm": bool(record.get("geomagnetic_storm", kp >= 5.0)),
        "severity": record.get("severity", "quiet"),
        "source": record.get("source", "unknown"),
        "_ingest_id": record.get("_ingest_id"),
        "_batch_id": record.get("_batch_id"),
    }
    return CleanResult.keep(out)


def silver_space_weather(records: list[dict[str, Any]]) -> SilverResult:
    return _apply(records, clean_space_weather, entity="silver_space_weather",
                  key_fields=["event_ts", "event_type"])


# --- Shared driver ----------------------------------------------------------

def _apply(records: list[dict[str, Any]], cleaner: Callable[[dict[str, Any]], CleanResult],
           *, entity: str, key_fields: list[str]) -> SilverResult:
    kept: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    for rec in records:
        result = cleaner(rec)
        if result.rejected or result.record is None:
            quarantine.append(_quarantine(rec, result.reasons, entity))
        else:
            kept.append(result.record)
    # Dedup keeps latest by event time per natural key.
    deduped = deduplicate(kept, key_fields=key_fields, order_field="event_ts")
    return SilverResult(entity=entity, rows=deduped, quarantine=quarantine)


# --- Spark entrypoint (requires infrastructure) -----------------------------

def run_spark(entity: str) -> None:  # pragma: no cover - needs Spark/MinIO
    """Read Bronze, apply the matching Silver transform, write Silver Parquet.

    Implemented as a thin wrapper that reuses the pure-Python cleaners as Spark
    ``mapInPandas`` logic so behaviour is identical to the offline path. Only
    runs when Spark + the object store are available.
    """
    from pyspark.sql import functions as F  # noqa: F401

    from transformation.common.spark import build_spark_session
    from transformation.config.settings import settings

    transforms = {
        "telemetry": ("satellite_telemetry", silver_telemetry),
        "orbit": ("orbit_position", silver_orbit),
        "space_weather": ("space_weather", silver_space_weather),
    }
    if entity not in transforms:
        raise ValueError(f"unknown entity: {entity}")
    dataset, fn = transforms[entity]

    spark = build_spark_session(f"silver-{entity}")
    bronze_path = settings.lake.path("bronze", dataset)
    silver_path = settings.lake.path("silver", f"silver_{entity}")

    bronze = spark.read.json(bronze_path)
    records = [r.asDict(recursive=True) for r in bronze.collect()]
    from transformation.common.io import unwrap_bronze

    result = fn([unwrap_bronze(r) for r in records])
    spark.createDataFrame(result.rows).write.mode("overwrite").parquet(silver_path)
    spark.stop()
