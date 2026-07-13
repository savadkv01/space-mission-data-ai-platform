"""Shared parsing for Sentinel Hub Statistical-API buckets (Phase 9b).

Both ``obs_aerosol`` (MODIS/VIIRS AOD) and ``obs_atmos_column`` (TROPOMI) land as
Statistical-API *buckets* — the identical response shape the existing
``obs_index`` cleaner reads. These helpers extract the per-bucket statistics,
the interval timestamp, and an AOI-centroid ``geo_key`` so the two cleaners stay
consistent with :func:`transformation.batch.bronze_to_silver.clean_index`.
"""

from __future__ import annotations

from typing import Any

from transformation.cleaning.cleaning_rules import normalize_timestamp, to_float
from transformation.geospatial.spatial_transform import clamp_lat, geo_key, normalize_lon


def bucket_stats(record: dict[str, Any]) -> dict[str, Any]:
    """Return the first output band's ``stats`` dict from a statistical bucket."""
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


def bucket_interval_ts(record: dict[str, Any]) -> str | None:
    """Normalized UTC timestamp of the bucket interval start."""
    interval = record.get("interval") or {}
    return normalize_timestamp(interval.get("from") or record.get("_event_ts"))


def valid_fraction(stats: dict[str, Any]) -> float | None:
    """``sampleCount / (sampleCount + noDataCount)`` — retrieval completeness."""
    sample = to_float(stats.get("sampleCount")) or 0.0
    nodata = to_float(stats.get("noDataCount")) or 0.0
    total = sample + nodata
    return round(sample / total, 4) if total > 0 else None


def bbox_centroid_geo_key(bbox: Any) -> tuple[str | None, str | None]:
    """Return ``(bbox_str, geo_key)`` for a stamped ``[minx,miny,maxx,maxy]`` bbox."""
    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        minx, miny, maxx, maxy = (to_float(v) for v in bbox)
    elif isinstance(bbox, str):
        parts = bbox.split(",")
        if len(parts) != 4:
            return None, None
        minx, miny, maxx, maxy = (to_float(p) for p in parts)
    else:
        return None, None
    if None in (minx, miny, maxx, maxy):
        return None, None
    bbox_str = f"{minx},{miny},{maxx},{maxy}"
    cx = normalize_lon((minx + maxx) / 2.0)
    cy = clamp_lat((miny + maxy) / 2.0)
    return bbox_str, geo_key(cy, cx)
