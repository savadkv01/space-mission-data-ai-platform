"""``obs_aerosol`` cleaner — MODIS/VIIRS Aerosol Optical Depth (Phase 9b).

Conforms one Sentinel-Hub Statistical-API AOD bucket (MODIS/VIIRS, unwrapped
from Bronze) to the Silver ``obs_aerosol`` schema: AOD at 550 nm per AOI per day
with QA filtering and desert bright-surface flagging.

Grain: 1 row / AOI / sensor / day. Natural key hashes (aoi_id, sensor, stat_date).

QA rules (docs/data-modeling/climate/02-silver-entities.md,
05-kpi-thresholds.md):

* AOD must fall in ``[0, 5]`` — out-of-range retrievals are rejected.
* Low retrieval completeness (``valid_fraction`` below the coverage threshold)
  or a desert bright-surface bias is *flagged* ``suspect`` — kept, not dropped,
  so downstream dust logic can corroborate it against the UV aerosol index.
"""

from __future__ import annotations

from typing import Any

from transformation.cleaning.cleaning_rules import CleanResult, stable_key, to_float
from transformation.cleaning.climate.buckets import (
    bbox_centroid_geo_key,
    bucket_interval_ts,
    bucket_stats,
    valid_fraction,
)

#: AOD physical range; retrievals outside this band are non-physical.
AOD_MIN, AOD_MAX = 0.0, 5.0

#: Below this valid-pixel fraction the AOD aggregate is flagged low-confidence.
MIN_VALID_FRACTION = 0.5


def clean_aerosol(record: dict[str, Any]) -> CleanResult:
    """Conform a MODIS/VIIRS AOD bucket to the Silver ``obs_aerosol`` schema."""
    ts = bucket_interval_ts(record)
    aoi_id = record.get("aoi_id")
    sensor = str(record.get("sensor") or "MODIS").upper()
    stats = bucket_stats(record)
    aod = to_float(stats.get("mean"))

    reasons: list[str] = []
    if ts is None:
        reasons.append("timestamp:unparseable")
    if aoi_id in (None, ""):
        reasons.append("null:aoi_id")
    if aod is None:
        reasons.append("null:aod")
    elif not (AOD_MIN <= aod <= AOD_MAX):
        reasons.append("range:aod")
    if reasons:
        return CleanResult.reject(reasons)

    bbox_str, geo_key_val = bbox_centroid_geo_key(record.get("bbox"))
    vfrac = valid_fraction(stats)
    bright_surface = bool(record.get("bright_surface_flag"))
    qa_mask = record.get("qa_mask") or None
    quality_flag = "valid"
    if bright_surface or (vfrac is not None and vfrac < MIN_VALID_FRACTION):
        quality_flag = "suspect"
    if qa_mask is None and record.get("collection") == "MODIS/061/MCD19A2_GRANULES":
        # Legacy MAIAC pull averaged all pixels (cloud/low-quality included).
        quality_flag = "suspect"

    stat_date = ts[:10]
    out = {
        "aerosol_key": stable_key(aoi_id, sensor, stat_date),
        "stat_date": stat_date,
        "event_ts": ts,
        "aoi_id": aoi_id,
        "geo_key": geo_key_val,
        "bbox": bbox_str,
        "sensor": sensor,
        "aod_550nm": round(aod, 6),
        "angstrom_exponent": to_float(record.get("angstrom_exponent")),
        # UV aerosol index is denormalized from obs_atmos_column (AER_AI) later.
        "uv_aerosol_index": to_float(record.get("uv_aerosol_index")),
        "bright_surface_flag": bright_surface,
        "valid_fraction": vfrac,
        "quality_flag": quality_flag,
        "qa_mask": qa_mask,
        "source": record.get("_source") or "MODIS_AOD",
        "_ingest_id": record.get("_ingest_id"),
        "_batch_id": record.get("_batch_id"),
    }
    return CleanResult.keep(out)
