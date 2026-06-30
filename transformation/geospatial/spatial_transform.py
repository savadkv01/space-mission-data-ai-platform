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
