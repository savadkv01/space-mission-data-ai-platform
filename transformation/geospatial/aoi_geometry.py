"""AOI geometry guard for request-based Silver entities (ADR-12).

MODIS AOD, TROPOMI, NASA POWER wind and GFW 4Wings records are AOI *means or
sums over the request box* stamped at ingestion. When an AOI is redrawn, Bronze
still holds records computed over the old box under the same ``aoi_id``; mixing
them with new-geometry records would silently change the meaning of a series.
Silver therefore keeps a record only if its AOI is still in the reference seed
and its stamped geometry matches the seed's current box.
"""

from __future__ import annotations

from typing import Any

from transformation.cleaning.cleaning_rules import to_float

#: Degrees; seed and connector boxes are written with at most 2 decimals.
BBOX_TOLERANCE_DEG = 1e-6
#: Degrees; NASA POWER requests a point at the box centroid (rounded upstream).
POINT_TOLERANCE_DEG = 0.01


def aoi_bbox_index(aois: list[dict[str, Any]] | None) -> dict[str, list[float]]:
    """``aoi_key -> [w, s, e, n]`` from the AOI reference seed."""
    out: dict[str, list[float]] = {}
    for aoi in aois or []:
        bbox = aoi.get("bbox")
        if aoi.get("aoi_key") and isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            out[aoi["aoi_key"]] = [float(v) for v in bbox]
    return out


def _parse_bbox(value: Any) -> list[float] | None:
    if isinstance(value, str):
        value = value.split(",")
    if isinstance(value, (list, tuple)) and len(value) == 4:
        parsed = [to_float(v) for v in value]
        if all(v is not None for v in parsed):
            return parsed  # type: ignore[return-value]
    return None


def bbox_geometry_reason(aoi_id: Any, bbox: Any,
                         index: dict[str, list[float]]) -> str | None:
    """Quarantine reason for a box-stamped record, or ``None`` to keep it.

    An empty ``index`` (no seed available) disables the guard. A record without
    a stamped box is kept: its geometry cannot be checked.
    """
    if not index or not aoi_id:
        return None
    current = index.get(str(aoi_id))
    if current is None:
        return "retired:aoi"
    stamped = _parse_bbox(bbox)
    if stamped is None:
        return None
    if any(abs(a - b) > BBOX_TOLERANCE_DEG for a, b in zip(stamped, current)):
        return "superseded:aoi_geometry"
    return None


def point_geometry_reason(aoi_id: Any, lat: Any, lon: Any,
                          index: dict[str, list[float]]) -> str | None:
    """Like :func:`bbox_geometry_reason` for records requested at the box centroid."""
    if not index or not aoi_id:
        return None
    current = index.get(str(aoi_id))
    if current is None:
        return "retired:aoi"
    y, x = to_float(lat), to_float(lon)
    if y is None or x is None:
        return None
    cy, cx = (current[1] + current[3]) / 2.0, (current[0] + current[2]) / 2.0
    if abs(y - cy) > POINT_TOLERANCE_DEG or abs(x - cx) > POINT_TOLERANCE_DEG:
        return "superseded:aoi_geometry"
    return None
