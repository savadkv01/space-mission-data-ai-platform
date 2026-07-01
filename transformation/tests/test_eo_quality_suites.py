"""Tests for the Phase 10 Earth-observation quality suites.

Pure-Python, offline. Verifies that each Silver/Gold suite passes on clean
sample batches and fails (critically) on injected quality defects that mirror the
documented rules in ``quality/rules/earth-observation-quality-rules.md``.
"""

from __future__ import annotations

from transformation.cleaning.validation_framework import run_checkpoint
from transformation.quality.eo_suites import (
    GOLD_SUITES,
    SILVER_SUITES,
    gold_flood_aoi_suite,
    gold_wildfire_aoi_suite,
    ref_aoi_suite,
    silver_fire_suite,
    silver_index_suite,
    silver_scene_suite,
    silver_vessel_suite,
)


# --- fixtures (inline sample rows) ------------------------------------------

def _fire_rows():
    return [
        {"fire_key": "a1", "event_ts": "2026-06-01T12:00:00Z", "latitude": 34.1,
         "longitude": -118.2, "geo_key": "g1", "frp": 12.5, "confidence": 80,
         "brightness": 320.0},
        {"fire_key": "a2", "event_ts": "2026-06-01T12:05:00Z", "latitude": 34.2,
         "longitude": -118.3, "geo_key": "g1", "frp": 0.0, "confidence": 33,
         "brightness": 300.0},
    ]


def _vessel_rows():
    return [
        {"vessel_key": "111", "mmsi": "111", "imo": "9999999", "flag": "USA",
         "first_transmission_ts": "2026-05-01T00:00:00Z",
         "last_transmission_ts": "2026-06-01T00:00:00Z",
         "event_ts": "2026-06-01T00:00:00Z"},
        {"vessel_key": "222", "mmsi": "222", "imo": None, "flag": None,
         "first_transmission_ts": None,
         "last_transmission_ts": "2026-06-02T00:00:00Z",
         "event_ts": "2026-06-02T00:00:00Z"},
    ]


def _scene_rows():
    return [
        {"scene_key": "S2A_1", "event_ts": "2026-06-01T10:00:00Z",
         "collection": "sentinel-2-l2a", "geo_key": "g1", "cloud_cover": 12.0,
         "completeness_score": 1.0},
    ]


def _index_rows():
    return [
        {"event_ts": "2026-06-01T10:00:00Z", "index_name": "NDWI", "mean": 0.3,
         "geo_key": "g1", "valid_pixel_fraction": 0.9},
        {"event_ts": "2026-06-02T10:00:00Z", "index_name": "NDVI", "mean": -0.1,
         "geo_key": "g2", "valid_pixel_fraction": 0.6},
    ]


def _aoi_rows():
    return [
        {"aoi_key": "AOI-1", "geo_key": "g1", "event_type": "fire", "area_km2": 42.0},
        {"aoi_key": "AOI-2", "geo_key": "g2", "event_type": "flood", "area_km2": 10.0},
    ]


# --- Silver: clean batches pass ---------------------------------------------

def test_silver_fire_clean_passes():
    result = run_checkpoint(_fire_rows(), silver_fire_suite(), "silver_fire")
    assert result.passed, result.failures


def test_silver_vessel_clean_passes():
    result = run_checkpoint(_vessel_rows(), silver_vessel_suite(), "silver_vessel")
    assert result.passed, result.failures


def test_silver_scene_clean_passes():
    result = run_checkpoint(_scene_rows(), silver_scene_suite(), "silver_scene")
    assert result.passed, result.failures


def test_silver_index_clean_passes():
    result = run_checkpoint(_index_rows(), silver_index_suite(), "silver_index")
    assert result.passed, result.failures


def test_ref_aoi_clean_passes():
    result = run_checkpoint(_aoi_rows(), ref_aoi_suite(), "ref_aoi")
    assert result.passed, result.failures


# --- Silver: injected defects fail critically -------------------------------

def test_fire_out_of_range_latitude_fails():
    rows = _fire_rows()
    rows[0]["latitude"] = 999
    result = run_checkpoint(rows, silver_fire_suite(), "silver_fire")
    assert not result.passed
    assert any("latitude" in f for f in result.failures)


def test_fire_negative_frp_fails():
    rows = _fire_rows()
    rows[0]["frp"] = -5
    result = run_checkpoint(rows, silver_fire_suite(), "silver_fire")
    assert not result.passed
    assert any("frp" in f for f in result.failures)


def test_fire_duplicate_key_fails():
    rows = _fire_rows()
    rows[1]["fire_key"] = rows[0]["fire_key"]
    result = run_checkpoint(rows, silver_fire_suite(), "silver_fire")
    assert not result.passed
    assert any("unique" in f for f in result.failures)


def test_vessel_timeline_regression_fails():
    rows = _vessel_rows()
    rows[0]["first_transmission_ts"] = "2027-01-01T00:00:00Z"  # after last
    result = run_checkpoint(rows, silver_vessel_suite(), "silver_vessel")
    assert not result.passed
    assert any("timeline" in f for f in result.failures)


def test_index_mean_out_of_bounds_fails():
    rows = _index_rows()
    rows[0]["mean"] = 5.0  # NDWI must be in [-1, 1]
    result = run_checkpoint(rows, silver_index_suite(), "silver_index")
    assert not result.passed
    assert any("mean" in f for f in result.failures)


def test_index_low_coverage_warns_not_fails():
    rows = _index_rows()
    rows[0]["valid_pixel_fraction"] = 0.05  # below 0.2 warn band, above 0 hard band
    result = run_checkpoint(rows, silver_index_suite(), "silver_index")
    assert result.passed  # warn only
    assert any("valid_pixel_fraction" in w for w in result.warnings)


def test_scene_cloud_cover_out_of_range_fails():
    rows = _scene_rows()
    rows[0]["cloud_cover"] = 250
    result = run_checkpoint(rows, silver_scene_suite(), "silver_scene")
    assert not result.passed


# --- Gold: business rules & referential integrity ---------------------------

def test_gold_scene_catalog_searchable_consistency():
    rows = [
        {"scene_key": "s1", "geo_key": "g1", "date_key": "2026-06-01",
         "collection": "sentinel-2-l2a", "cloud_cover": 5.0,
         "completeness_score": 1.0, "is_searchable": True},
    ]
    result = run_checkpoint(rows, GOLD_SUITES["fact_scene_catalog"](),
                            "fact_scene_catalog")
    assert result.passed, result.failures

    rows[0]["is_searchable"] = False  # inconsistent with populated keys
    result = run_checkpoint(rows, GOLD_SUITES["fact_scene_catalog"](),
                            "fact_scene_catalog")
    assert not result.passed
    assert any("searchable" in f for f in result.failures)


def test_gold_wildfire_aoi_referential_integrity():
    ref_keys = {"AOI-1", "AOI-2"}
    rows = [
        {"aoi_key": "AOI-1", "date_key": "2026-06-01", "detections": 3,
         "mean_frp": 10.0, "max_frp": 20.0},
    ]
    result = run_checkpoint(rows, gold_wildfire_aoi_suite(ref_keys),
                            "kpi_wildfire_aoi_daily")
    assert result.passed, result.failures

    rows.append({"aoi_key": "AOI-UNKNOWN", "date_key": "2026-06-01",
                 "detections": 1, "mean_frp": 1.0, "max_frp": 1.0})
    result = run_checkpoint(rows, gold_wildfire_aoi_suite(ref_keys),
                            "kpi_wildfire_aoi_daily")
    assert not result.passed
    assert any("referential_integrity" in f for f in result.failures)


def test_gold_flood_aoi_ndwi_bounds():
    rows = [
        {"aoi_key": "AOI-2", "date_key": "2026-06-01", "ndwi_mean": 0.4,
         "valid_pixel_fraction": 0.8},
    ]
    result = run_checkpoint(rows, gold_flood_aoi_suite(), "kpi_flood_aoi_daily")
    assert result.passed, result.failures

    rows[0]["ndwi_mean"] = 3.0
    result = run_checkpoint(rows, gold_flood_aoi_suite(), "kpi_flood_aoi_daily")
    assert not result.passed


def test_registries_cover_expected_entities():
    assert set(SILVER_SUITES) == {
        "silver_fire", "silver_vessel", "silver_scene", "silver_index", "ref_aoi"}
    assert set(GOLD_SUITES) == {
        "kpi_eo_daily", "fact_vessel_activity", "fact_scene_catalog",
        "kpi_wildfire_aoi_daily", "kpi_flood_aoi_daily"}
