from __future__ import annotations

import math

from transformation.geospatial.spatial_transform import (
    assign_aoi,
    geo_key,
    haversine_km,
    normalize_lon,
    normalize_position,
    point_in_polygon,
    polygon_area_km2,
    reconstruct_path_length_km,
    snap_to_grid,
)

_SQUARE = [[[54.8, 24.8], [55.6, 24.8], [55.6, 25.5], [54.8, 25.5], [54.8, 24.8]]]
_AOI = {"aoi_key": "EMSR001", "bbox": [54.8, 24.8, 55.6, 25.5], "polygons": [_SQUARE]}


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


def test_point_in_polygon_inside_and_outside():
    assert point_in_polygon(55.0, 25.0, _SQUARE) is True
    assert point_in_polygon(10.0, 10.0, _SQUARE) is False


def test_point_in_polygon_respects_holes():
    hole = [[54.9, 24.9], [55.5, 24.9], [55.5, 25.4], [54.9, 25.4], [54.9, 24.9]]
    with_hole = [_SQUARE[0], hole]
    assert point_in_polygon(55.0, 25.0, with_hole) is False


def test_assign_aoi_matches_and_prefilters():
    assert assign_aoi(25.0, 55.0, [_AOI]) == ["EMSR001"]
    assert assign_aoi(10.0, 10.0, [_AOI]) == []  # bbox pre-filter rejects
    assert assign_aoi(None, None, [_AOI]) == []


def test_polygon_area_km2_positive():
    area = polygon_area_km2(_SQUARE)
    assert area > 0
    assert 1000 < area < 10000


def test_reconstruct_path_length():
    pts = [{"latitude": 0, "longitude": 0}, {"latitude": 0, "longitude": 1},
           {"latitude": 0, "longitude": 2}]
    assert reconstruct_path_length_km(pts) > 0
