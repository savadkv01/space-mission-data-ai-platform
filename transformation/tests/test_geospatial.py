from __future__ import annotations

import math

from transformation.geospatial.spatial_transform import (
    geo_key,
    haversine_km,
    normalize_lon,
    normalize_position,
    reconstruct_path_length_km,
    snap_to_grid,
)


def test_normalize_lon_wraps():
    assert normalize_lon(190) == -170
    assert normalize_lon(-190) == 170


def test_snap_to_grid_and_key():
    glat, glon = snap_to_grid(10.12, 20.04, cell_deg=0.25)
    assert glat == 10.0 and glon == 0.0 or (glat, glon) == (10.0, 20.0)
    assert isinstance(geo_key(10.12, 20.04), str)


def test_haversine_known_distance():
    # ~111 km per degree of latitude near the equator
    d = haversine_km(0, 0, 1, 0)
    assert math.isclose(d, 111.19, rel_tol=0.02)


def test_normalize_position_adds_geo_key():
    out = normalize_position({"latitude": 12.3456, "longitude": 200.0})
    assert out["longitude"] < 180
    assert "geo_key" in out and "grid_lat" in out


def test_reconstruct_path_length():
    pts = [{"latitude": 0, "longitude": 0}, {"latitude": 0, "longitude": 1},
           {"latitude": 0, "longitude": 2}]
    assert reconstruct_path_length_km(pts) > 0
