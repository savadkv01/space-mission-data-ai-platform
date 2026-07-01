"""Geospatial transformation primitives (Task 10).

Pure-Python, dependency-free geo helpers used by the orbit Silver transform and
the Earth-observation Gold marts. Heavier work (true reprojection, spatial
joins) is delegated to Spark + Sedona/H3 in the cluster jobs; these primitives
cover the WGS84 normalization, grid bucketing, and great-circle math needed for
the offline pipeline and tests.
"""

from __future__ import annotations

import math
from typing import Any

_EARTH_RADIUS_KM = 6371.0


def normalize_lon(lon: float) -> float:
    """Wrap longitude into [-180, 180)."""
    return ((lon + 180.0) % 360.0) - 180.0


def clamp_lat(lat: float) -> float:
    return max(-90.0, min(90.0, lat))


def snap_to_grid(lat: float, lon: float, cell_deg: float = 0.25) -> tuple[float, float]:
    """Round coordinates to a fixed grid (Task 9 geospatial aggregation).

    A 0.25-degree grid (~27 km at the equator) keeps the EO marts compact while
    preserving useful spatial resolution.
    """
    glat = round(lat / cell_deg) * cell_deg
    glon = round(lon / cell_deg) * cell_deg
    return round(glat, 4), round(glon, 4)


def geo_key(lat: float, lon: float, cell_deg: float = 0.25) -> str:
    """Stable string key for a grid cell, used for geospatial joins/aggregation."""
    glat, glon = snap_to_grid(lat, lon, cell_deg)
    return f"{glat:.4f}:{glon:.4f}"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def normalize_position(record: dict[str, Any], cell_deg: float = 0.25) -> dict[str, Any]:
    """Return a copy of an orbit/observation record with normalized geo fields.

    Adds ``geo_key`` and grid-snapped ``grid_lat``/``grid_lon`` columns and wraps
    longitude into the canonical range. Returns ``None`` geo fields untouched.
    """
    out = dict(record)
    lat, lon = record.get("latitude"), record.get("longitude")
    if lat is None or lon is None:
        return out
    lat = clamp_lat(float(lat))
    lon = normalize_lon(float(lon))
    glat, glon = snap_to_grid(lat, lon, cell_deg)
    out["latitude"] = round(lat, 5)
    out["longitude"] = round(lon, 5)
    out["grid_lat"] = glat
    out["grid_lon"] = glon
    out["geo_key"] = f"{glat:.4f}:{glon:.4f}"
    return out


def reconstruct_path_length_km(points: list[dict[str, Any]]) -> float:
    """Sum great-circle segments of an ordered orbit ground track (Task 10)."""
    total = 0.0
    for prev, cur in zip(points, points[1:]):
        if None in (prev.get("latitude"), prev.get("longitude"),
                    cur.get("latitude"), cur.get("longitude")):
            continue
        total += haversine_km(prev["latitude"], prev["longitude"],
                              cur["latitude"], cur["longitude"])
    return round(total, 3)


# --- AOI polygon geometry (point-in-polygon joins, Task 10) -----------------
#
# The cluster job resolves point/polygon joins with Sedona + H3; these
# dependency-free primitives implement the identical join for the offline path
# and the unit tests. Rings follow the GeoJSON convention: a list of
# ``[lon, lat]`` pairs. A polygon is ``[outer_ring, *hole_rings]``.

def ring_bbox(ring: list[list[float]]) -> tuple[float, float, float, float]:
    """Return ``(min_lon, min_lat, max_lon, max_lat)`` of a ring."""
    lons = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    return min(lons), min(lats), max(lons), max(lats)


def point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    """Ray-casting point-in-polygon test for a single ring."""
    n = len(ring)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi
        ):
            inside = not inside
        j = i
    return inside


def point_in_polygon(lon: float, lat: float, polygon: list[list[list[float]]]) -> bool:
    """True if the point is inside the outer ring and outside every hole."""
    if not polygon:
        return False
    if not point_in_ring(lon, lat, polygon[0]):
        return False
    return not any(point_in_ring(lon, lat, hole) for hole in polygon[1:])


def iter_geojson_polygons(geometry: dict[str, Any]):
    """Yield polygons (``[outer, *holes]``) from a GeoJSON geometry dict."""
    if not isinstance(geometry, dict):
        return
    gtype = geometry.get("type")
    coords = geometry.get("coordinates")
    if gtype == "Polygon" and isinstance(coords, list):
        yield coords
    elif gtype == "MultiPolygon" and isinstance(coords, list):
        for poly in coords:
            if isinstance(poly, list):
                yield poly


def polygon_area_km2(polygon: list[list[list[float]]]) -> float:
    """Approximate polygon area (outer minus holes) in km² via planar shoelace."""
    if not polygon or len(polygon[0]) < 3:
        return 0.0

    def _ring_area_deg2(ring: list[list[float]]) -> float:
        s = 0.0
        n = len(ring)
        for i in range(n):
            x1, y1 = ring[i][0], ring[i][1]
            x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
            s += x1 * y2 - x2 * y1
        return abs(s) / 2.0

    area_deg2 = max(_ring_area_deg2(polygon[0])
                    - sum(_ring_area_deg2(h) for h in polygon[1:]), 0.0)
    mean_lat = sum(p[1] for p in polygon[0]) / len(polygon[0])
    km_per_deg_lat = 110.574
    km_per_deg_lon = 111.320 * math.cos(math.radians(mean_lat))
    return round(area_deg2 * km_per_deg_lat * km_per_deg_lon, 4)


def assign_aoi(lat: float | None, lon: float | None,
               aois: list[dict[str, Any]]) -> list[str]:
    """Return the ``aoi_key`` of every AOI whose geometry contains the point.

    Each AOI dict carries ``aoi_key``, ``bbox`` (``[min_lon, min_lat, max_lon,
    max_lat]``) and ``polygons`` (list of GeoJSON polygons). The bbox pre-filter
    skips the ray cast for the common no-match case.
    """
    if lat is None or lon is None:
        return []
    matched: list[str] = []
    for aoi in aois:
        bbox = aoi.get("bbox")
        if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            if not (bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]):
                continue
        for polygon in aoi.get("polygons", []):
            if point_in_polygon(lon, lat, polygon):
                matched.append(aoi["aoi_key"])
                break
    return matched

