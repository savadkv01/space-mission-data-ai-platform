"""``obs_atmos_column`` cleaner — TROPOMI trace-gas columns (Phase 9b).

Conforms one Sentinel-Hub Statistical-API TROPOMI bucket (unwrapped from Bronze)
to the Silver ``obs_atmos_column`` schema: a trace-gas / aerosol-index **column
density** per AOI per day.

Grain: 1 row / AOI / gas / day. Natural key hashes (aoi_id, gas_code, stat_date).

Semantic guard: ``mean`` is a column density (mol/m², ppb for CH4, unitless for
AER_AI), *not* a surface concentration — never conformed to
``obs_air_quality.value_std``. Low-coverage rows (valid-pixel fraction below the
threshold) are flagged ``low_coverage`` rather than dropped so gaps stay visible.
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

#: Below this valid-pixel fraction a column bucket is flagged low_coverage.
MIN_VALID_PIXEL_FRACTION = 0.5

#: Canonical unit per trace-gas / aerosol product.
GAS_UNIT = {
    "NO2": "mol/m2",
    "SO2": "mol/m2",
    "CO": "mol/m2",
    "O3": "mol/m2",
    "CH4": "ppb",
    "AER_AI": "unitless",
}


def clean_atmos_column(record: dict[str, Any]) -> CleanResult:
    """Conform a TROPOMI bucket to the Silver ``obs_atmos_column`` schema."""
    ts = bucket_interval_ts(record)
    aoi_id = record.get("aoi_id")
    gas_code = str(record.get("product") or "").upper() or None
    stats = bucket_stats(record)
    mean = to_float(stats.get("mean"))

    reasons: list[str] = []
    if ts is None:
        reasons.append("timestamp:unparseable")
    if aoi_id in (None, ""):
        reasons.append("null:aoi_id")
    if gas_code is None or gas_code not in GAS_UNIT:
        reasons.append("unknown:gas")
    if mean is None:
        reasons.append("null:mean")
    if reasons:
        return CleanResult.reject(reasons)

    bbox_str, geo_key_val = bbox_centroid_geo_key(record.get("bbox"))
    vfrac = valid_fraction(stats)
    quality_flag = (
        "low_coverage"
        if vfrac is not None and vfrac < MIN_VALID_PIXEL_FRACTION
        else "valid"
    )
    stat_date = ts[:10]
    unit_std = record.get("unit") or GAS_UNIT[gas_code]

    out = {
        "atmos_key": stable_key(aoi_id, gas_code, stat_date),
        "stat_date": stat_date,
        "event_ts": ts,
        "aoi_id": aoi_id,
        "geo_key": geo_key_val,
        "bbox": bbox_str,
        "gas_code": gas_code,
        "mean": round(mean, 9),
        "min": to_float(stats.get("min")),
        "max": to_float(stats.get("max")),
        "stddev": to_float(stats.get("stDev")),
        "unit_std": unit_std,
        "valid_pixel_fraction": vfrac,
        "quality_flag": quality_flag,
        "source": record.get("_source") or "TROPOMI",
        "_ingest_id": record.get("_ingest_id"),
        "_batch_id": record.get("_batch_id"),
    }
    return CleanResult.keep(out)
