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
    clamp,
    deduplicate,
    in_range,
    normalize_timestamp,
    require_fields,
    stable_key,
    to_float,
)
from transformation.geospatial.spatial_transform import (
    clamp_lat,
    geo_key,
    iter_geojson_polygons,
    normalize_lon,
    normalize_position,
    polygon_area_km2,
)


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


# --- Earth observation: active fire (FIRMS / VIIRS) -------------------------

_CONFIDENCE_MAP = {"l": 33, "low": 33, "n": 66, "nominal": 66, "h": 99, "high": 99}


def _normalize_confidence(value: Any) -> int | None:
    """Map FIRMS confidence to a 0-100 int (VIIRS is nominal/low/high, MODIS numeric)."""
    if value in (None, ""):
        return None
    token = str(value).strip().lower()
    if token in _CONFIDENCE_MAP:
        return _CONFIDENCE_MAP[token]
    num = to_float(token)
    if num is None:
        return None
    return int(clamp(num, 0, 100))


def _fire_event_ts(record: dict[str, Any]) -> str | None:
    date = record.get("acq_date")
    if date:
        time = str(record.get("acq_time", "0")).zfill(4)
        return normalize_timestamp(f"{date}T{time[:2]}:{time[2:]}:00+00:00")
    return normalize_timestamp(record.get("_event_ts"))


def _fire_source(record: dict[str, Any]) -> str:
    instrument = str(record.get("instrument", "")).upper()
    if "VIIRS" in instrument:
        return "VIIRS"
    if "MODIS" in instrument:
        return "MODIS"
    src = str(record.get("_source", "")).upper()
    return "MODIS" if "MODIS" in src else "VIIRS"


def clean_fire(record: dict[str, Any]) -> CleanResult:
    """Conform a FIRMS/VIIRS active-fire detection to the Silver ``obs_fire`` schema."""
    reasons = require_fields(record, ["latitude", "longitude"])
    ts = _fire_event_ts(record)
    if ts is None:
        reasons.append("timestamp:unparseable")
    if not in_range(record.get("latitude"), -90, 90):
        reasons.append("range:latitude")
    if not in_range(record.get("longitude"), -180, 180):
        reasons.append("range:longitude")
    frp = to_float(record.get("frp"))
    if frp is not None and frp < 0:
        reasons.append("range:frp")
    if reasons:
        return CleanResult.reject(reasons)

    base = normalize_position({
        "latitude": to_float(record["latitude"]),
        "longitude": to_float(record["longitude"]),
    })
    satellite = str(record.get("satellite", "unknown"))
    daynight = str(record.get("daynight", "")).upper()[:1] or None
    out = {
        "fire_key": stable_key(base["latitude"], base["longitude"], ts, satellite),
        "event_ts": ts,
        "latitude": base["latitude"],
        "longitude": base["longitude"],
        "geo_key": base["geo_key"],
        "brightness": to_float(record.get("brightness")),
        "frp": frp,
        "confidence": _normalize_confidence(record.get("confidence")),
        "satellite": satellite,
        "daynight": daynight,
        "source": _fire_source(record),
        "_ingest_id": record.get("_ingest_id"),
        "_batch_id": record.get("_batch_id"),
    }
    return CleanResult.keep(out)


def silver_fire(records: list[dict[str, Any]]) -> SilverResult:
    return _apply(records, clean_fire, entity="silver_fire",
                  key_fields=["fire_key"])


# --- Maritime domain awareness: vessels (Global Fishing Watch) --------------

def _vessel_info(record: dict[str, Any]) -> dict[str, Any]:
    """Flatten the first GFW registry/self-reported block into scalar fields."""
    for block_key in ("registryInfo", "selfReportedInfo", "combinedSourcesInfo"):
        block = record.get(block_key)
        if isinstance(block, list) and block and isinstance(block[0], dict):
            entry = block[0]
            return {
                "mmsi": entry.get("ssvid") or entry.get("mmsi"),
                "imo": entry.get("imo"),
                "shipname": entry.get("shipname") or entry.get("nShipname"),
                "flag": entry.get("flag"),
                "vessel_type": entry.get("vesselType") or entry.get("shiptype"),
                "first_transmission": entry.get("transmissionDateFrom")
                or entry.get("firstTransmissionDate"),
                "last_transmission": entry.get("transmissionDateTo")
                or entry.get("lastTransmissionDate"),
            }
    return {
        "mmsi": record.get("mmsi") or record.get("ssvid"),
        "imo": record.get("imo"),
        "shipname": record.get("shipname"),
        "flag": record.get("flag"),
        "vessel_type": record.get("vessel_type") or record.get("vesselType"),
        "first_transmission": record.get("first_transmission"),
        "last_transmission": record.get("last_transmission"),
    }


def _clean_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def clean_vessel(record: dict[str, Any]) -> CleanResult:
    """Conform a GFW vessel-identity record to the Silver ``obs_vessel`` schema."""
    info = _vessel_info(record)
    reasons: list[str] = []
    mmsi = _clean_str(info.get("mmsi"))
    if mmsi is None:
        reasons.append("null:mmsi")
    last_ts = normalize_timestamp(info.get("last_transmission") or record.get("_event_ts"))
    if last_ts is None:
        reasons.append("timestamp:unparseable")
    if reasons:
        return CleanResult.reject(reasons)

    shipname = _clean_str(info.get("shipname"))
    flag = _clean_str(info.get("flag"))
    out = {
        "vessel_key": mmsi,
        "mmsi": mmsi,
        "imo": _clean_str(info.get("imo")),
        "shipname": shipname.upper() if shipname else None,
        "flag": flag.upper() if flag else None,
        "vessel_type": _clean_str(info.get("vessel_type")),
        "first_transmission_ts": normalize_timestamp(info.get("first_transmission")),
        "last_transmission_ts": last_ts,
        "event_ts": last_ts,
        "source": _clean_str(record.get("_source")) or "GFW",
        "_ingest_id": record.get("_ingest_id"),
        "_batch_id": record.get("_batch_id"),
    }
    return CleanResult.keep(out)


def silver_vessel(records: list[dict[str, Any]]) -> SilverResult:
    return _apply(records, clean_vessel, entity="silver_vessel",
                  key_fields=["vessel_key"])


# --- Scene metadata catalog (Sentinel Hub / Earthdata) ----------------------

_SCENE_META_FIELDS = ("collection", "platform", "bbox", "geo_key", "cloud_cover")


def _scene_geo(record: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return (bbox_str, geo_key) from a STAC ``bbox`` or a CMR ``boxes`` string."""
    bbox = record.get("bbox")
    minx = miny = maxx = maxy = None
    if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
        minx, miny, maxx, maxy = (to_float(bbox[0]), to_float(bbox[1]),
                                  to_float(bbox[2]), to_float(bbox[3]))
    else:
        # CMR granules express footprints as "S W N E" strings.
        boxes = record.get("boxes")
        if isinstance(boxes, list) and boxes:
            parts = str(boxes[0]).split()
            if len(parts) == 4:
                south, west, north, east = (to_float(p) for p in parts)
                minx, miny, maxx, maxy = west, south, east, north
    if None in (minx, miny, maxx, maxy):
        return None, None
    bbox_str = f"{minx},{miny},{maxx},{maxy}"
    cx = normalize_lon((minx + maxx) / 2.0)
    cy = clamp_lat((miny + maxy) / 2.0)
    return bbox_str, geo_key(cy, cx)


def clean_scene_metadata(record: dict[str, Any]) -> CleanResult:
    """Conform an imagery scene/granule to the Silver ``obs_scene`` schema.

    Source-agnostic: accepts STAC features (Sentinel Hub, LandsatLook) and CMR
    granule entries (NASA Earthdata) by falling back across their field names.
    """
    props = record.get("properties") or {}
    scene_id = _clean_str(
        record.get("id") or record.get("scene_id")
        or record.get("producer_granule_id") or record.get("title")
    )
    reasons: list[str] = []
    if scene_id is None:
        reasons.append("null:scene_id")
    ts = normalize_timestamp(
        props.get("datetime") or record.get("time_start") or record.get("_event_ts")
    )
    if ts is None:
        reasons.append("timestamp:unparseable")
    if reasons:
        return CleanResult.reject(reasons)

    bbox_str, geo_key_val = _scene_geo(record)
    cloud = to_float(
        props.get("eo:cloud_cover", props.get("cloud_cover", record.get("cloud_cover")))
    )
    out = {
        "scene_key": scene_id,
        "event_ts": ts,
        "collection": _clean_str(
            record.get("collection") or props.get("collection") or record.get("dataset_id")
        ),
        "platform": _clean_str(props.get("platform") or record.get("platforms")),
        "bbox": bbox_str,
        "geo_key": geo_key_val,
        "cloud_cover": clamp(cloud, 0, 100) if cloud is not None else None,
        "provider": _clean_str(props.get("provider")) or _clean_str(record.get("_source")),
        "source": _clean_str(record.get("_source")) or "SENTINELHUB",
        "_ingest_id": record.get("_ingest_id"),
        "_batch_id": record.get("_batch_id"),
    }
    present = sum(1 for f in _SCENE_META_FIELDS if out.get(f) not in (None, ""))
    out["completeness_score"] = round(present / len(_SCENE_META_FIELDS), 3)
    return CleanResult.keep(out)


def silver_scene(records: list[dict[str, Any]]) -> SilverResult:
    return _apply(records, clean_scene_metadata, entity="silver_scene",
                  key_fields=["scene_key"])


# --- Spectral index statistics (Sentinel Hub Statistical API) ---------------

def _index_stats(record: dict[str, Any]) -> dict[str, Any]:
    """Pull the first output band's ``stats`` dict from a statistical bucket."""
    outputs = record.get("outputs") or {}
    if isinstance(outputs, dict):
        for out in outputs.values():
            bands = out.get("bands") if isinstance(out, dict) else None
            if isinstance(bands, dict):
                for band in bands.values():
                    stats = band.get("stats") if isinstance(band, dict) else None
                    if isinstance(stats, dict):
                        return stats
    return {}


def clean_index(record: dict[str, Any]) -> CleanResult:
    """Conform a Sentinel Hub statistical bucket to the Silver ``obs_index`` schema.

    Grain is one row per AOI / index / date bucket. ``valid_pixel_fraction``
    reports data coverage so downstream features can drop cloud-masked windows.
    """
    interval = record.get("interval") or {}
    ts = normalize_timestamp(interval.get("from") or record.get("_event_ts"))
    index_name = _clean_str(record.get("index"))
    stats = _index_stats(record)
    mean = to_float(stats.get("mean"))
    bbox_str, geo_key_val = _scene_geo(record)

    reasons: list[str] = []
    if ts is None:
        reasons.append("timestamp:unparseable")
    if index_name is None:
        reasons.append("null:index")
    if mean is None:
        reasons.append("null:mean")
    if geo_key_val is None:
        reasons.append("null:geo_key")
    if reasons:
        return CleanResult.reject(reasons)

    sample = to_float(stats.get("sampleCount")) or 0.0
    nodata = to_float(stats.get("noDataCount")) or 0.0
    total = sample + nodata
    valid_fraction = round(sample / total, 4) if total > 0 else None
    stat_date = ts[:10]
    index_upper = index_name.upper()
    out = {
        "index_key": stable_key(geo_key_val, index_upper, stat_date),
        "index_name": index_upper,
        "stat_date": stat_date,
        "event_ts": ts,
        "geo_key": geo_key_val,
        "bbox": bbox_str,
        "mean": mean,
        "min": to_float(stats.get("min")),
        "max": to_float(stats.get("max")),
        "stddev": to_float(stats.get("stDev")),
        "valid_pixel_fraction": valid_fraction,
        "collection": _clean_str(record.get("collection")),
        "source": _clean_str(record.get("_source")) or "SENTINELHUB_STATS",
        "_ingest_id": record.get("_ingest_id"),
        "_batch_id": record.get("_batch_id"),
    }
    return CleanResult.keep(out)


def silver_index(records: list[dict[str, Any]]) -> SilverResult:
    return _apply(records, clean_index, entity="silver_index",
                  key_fields=["index_key"])


# --- AOI reference layer (Copernicus EMS footprints) ------------------------

def _ems_event_type(props: dict[str, Any]) -> str:
    """Classify an EMS activation into flood / fire / other."""
    blob = " ".join(str(props.get(k, "")) for k in (
        "eventType", "event_type", "hazard", "type", "category", "name", "aoiName"
    )).lower()
    if any(w in blob for w in ("flood", "inundation", "water")):
        return "flood"
    if any(w in blob for w in ("fire", "wildfire", "burn")):
        return "fire"
    return "other"


def _expand_feature_collections(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten GeoJSON FeatureCollections into individual Features.

    A landed EMS file arrives as one Bronze record holding a FeatureCollection;
    provenance columns are carried down onto each expanded Feature.
    """
    out: list[dict[str, Any]] = []
    for rec in records:
        if isinstance(rec, dict) and rec.get("type") == "FeatureCollection":
            for feat in rec.get("features", []) or []:
                if isinstance(feat, dict):
                    merged = dict(feat)
                    for col in ("_ingest_id", "_batch_id", "_source", "_event_ts"):
                        merged.setdefault(col, rec.get(col))
                    out.append(merged)
        else:
            out.append(rec)
    return out


def clean_ems_aoi(record: dict[str, Any]) -> CleanResult:
    """Conform a Copernicus EMS GeoJSON Feature to the Silver ``ref_aoi`` schema.

    EMS rapid-mapping footprints act both as monitored AOIs and as independent
    validation ground truth for wildfire (UC-15) and flood (UC-16) detections.
    """
    props = record.get("properties") or {}
    geometry = record.get("geometry") or {}
    polygons = list(iter_geojson_polygons(geometry))
    aoi_id = _clean_str(
        props.get("id") or props.get("aoiId") or props.get("name")
        or props.get("aoiName") or record.get("id")
    )

    reasons: list[str] = []
    if aoi_id is None:
        reasons.append("null:aoi_id")
    if not polygons:
        reasons.append("null:geometry")
    if reasons:
        return CleanResult.reject(reasons)

    outer_pts = [pt for poly in polygons for pt in poly[0]]
    lons = [p[0] for p in outer_pts]
    lats = [p[1] for p in outer_pts]
    bbox = [min(lons), min(lats), max(lons), max(lats)]
    cx = normalize_lon((bbox[0] + bbox[2]) / 2.0)
    cy = clamp_lat((bbox[1] + bbox[3]) / 2.0)
    event_date = normalize_timestamp(
        props.get("eventDate") or props.get("event_time")
        or props.get("date") or record.get("_event_ts")
    )
    out = {
        "aoi_key": aoi_id,
        "aoi_name": _clean_str(props.get("name") or props.get("aoiName")) or aoi_id,
        "event_type": _ems_event_type(props),
        "event_date": event_date,
        "event_ts": event_date,
        "bbox": bbox,
        "geo_key": geo_key(cy, cx),
        "polygons": polygons,
        "area_km2": round(sum(polygon_area_km2(p) for p in polygons), 4),
        "source": _clean_str(record.get("_source")) or "EMS",
        "_ingest_id": record.get("_ingest_id"),
        "_batch_id": record.get("_batch_id"),
    }
    return CleanResult.keep(out)


def silver_ems_aoi(records: list[dict[str, Any]]) -> SilverResult:
    return _apply(_expand_feature_collections(records), clean_ems_aoi,
                  entity="silver_ems_aoi", key_fields=["aoi_key"])


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
        "telemetry": (["satellite_telemetry"], silver_telemetry),
        "orbit": (["orbit_position"], silver_orbit),
        "space_weather": (["space_weather"], silver_space_weather),
        "fire": (["FIRMS"], silver_fire),
        "vessel": (["GFW"], silver_vessel),
        # Imagery metadata from every source unions into one obs_scene entity.
        "scene": (["SENTINELHUB", "LANDSAT", "EARTHDATA"], silver_scene),
        # Spectral index statistics (NDVI/NDWI/NBR) per AOI/date.
        "index": (["SENTINELHUB_STATS"], silver_index),
        # AOI reference footprints from Copernicus EMS (validation ground truth).
        "ems_aoi": (["EMS"], silver_ems_aoi),
    }
    if entity not in transforms:
        raise ValueError(f"unknown entity: {entity}")
    datasets, fn = transforms[entity]

    spark = build_spark_session(f"silver-{entity}")
    silver_path = settings.lake.path("silver", f"silver_{entity}")

    from transformation.common.io import unwrap_bronze

    records: list[dict[str, Any]] = []
    for dataset in datasets:
        bronze = spark.read.json(settings.lake.path("bronze", dataset))
        records.extend(r.asDict(recursive=True) for r in bronze.collect())

    result = fn([unwrap_bronze(r) for r in records])
    spark.createDataFrame(result.rows).write.mode("overwrite").parquet(silver_path)
    spark.stop()
