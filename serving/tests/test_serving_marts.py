"""Data-product + serving-model tests (Task 4 deliverable: view tests).

These run offline (pure-Python) against the exact Gold field names produced by
``transformation.batch.silver_to_gold`` so the serving contracts stay pinned to
real Gold output.
"""

from __future__ import annotations

from serving.marts import serving_marts as sm


# --- MVP Earth-observation products ---------------------------------------- #

def test_wildfire_enriches_and_bands_severity():
    wildfire = [{"aoi_key": "EMS-A", "date_key": "2026-06-01",
                 "detections": 12, "mean_frp": 40.0, "max_frp": 120.0}]
    aoi_dim = [{"aoi_key": "EMS-A", "aoi_name": "Attica Fire", "area_km2": 55.0}]
    validation = [{"aoi_key": "EMS-A", "event_type": "fire", "corroborated": True}]

    rows = sm.serve_wildfire_daily(wildfire, aoi_dim, validation)
    assert len(rows) == 1
    r = rows[0]
    assert r["aoi_name"] == "Attica Fire"
    assert r["area_km2"] == 55.0
    assert r["severity"] == "extreme"        # max_frp >= 100
    assert r["ems_corroborated"] is True


def test_wildfire_missing_dim_and_frp_is_safe():
    rows = sm.serve_wildfire_daily(
        [{"aoi_key": "X", "date_key": "2026-06-01", "detections": 1}])
    r = rows[0]
    assert r["aoi_name"] is None
    assert r["severity"] == "unknown"
    assert r["ems_corroborated"] is False


def test_flood_flag_and_corroboration():
    flood = [{"aoi_key": "EMS-F", "date_key": "2026-06-02",
              "ndwi_mean": 0.2, "ndwi_max": 0.4,
              "valid_pixel_fraction": 0.9, "flood_flag": True}]
    validation = [{"aoi_key": "EMS-F", "event_type": "flood", "corroborated": True}]
    rows = sm.serve_flood_daily(flood, None, validation)
    assert rows[0]["flood_flag"] is True
    assert rows[0]["ems_corroborated"] is True


def test_flood_corroboration_ignores_wrong_event_type():
    validation = [{"aoi_key": "EMS-F", "event_type": "fire", "corroborated": True}]
    rows = sm.serve_flood_daily(
        [{"aoi_key": "EMS-F", "date_key": "d", "flood_flag": False}], None, validation)
    assert rows[0]["ems_corroborated"] is False


def test_vessel_review_priority_from_suspicious():
    vessels = [
        {"vessel_key": "V1", "date_key": "d", "transmissions": 3, "suspicious_flag": True},
        {"vessel_key": "V2", "date_key": "d", "transmissions": 5, "suspicious_flag": False},
    ]
    rows = sm.serve_vessel_activity(vessels)
    by_key = {r["vessel_key"]: r for r in rows}
    assert by_key["V1"]["review_priority"] == "high"
    assert by_key["V2"]["review_priority"] == "normal"


def test_scene_catalog_quality_bands():
    scenes = [
        {"scene_key": "S1", "completeness_score": 0.95, "is_searchable": True},
        {"scene_key": "S2", "completeness_score": 0.75, "is_searchable": True},
        {"scene_key": "S3", "completeness_score": 0.5, "is_searchable": True},
        {"scene_key": "S4", "completeness_score": 0.99, "is_searchable": False},
    ]
    bands = {r["scene_key"]: r["quality_band"] for r in sm.serve_scene_catalog(scenes)}
    assert bands == {"S1": "gold", "S2": "silver", "S3": "bronze", "S4": "unlisted"}


def test_aoi_validation_trust_label():
    rows = sm.serve_aoi_validation([
        {"aoi_key": "A", "event_type": "fire", "corroborated": True, "evidence_days": 3},
        {"aoi_key": "B", "event_type": "flood", "corroborated": False, "evidence_days": 0},
    ])
    trust = {r["aoi_key"]: r["trust"] for r in rows}
    assert trust == {"A": "corroborated", "B": "unconfirmed"}


# --- Simulation-Track products --------------------------------------------- #

def test_satellite_health_status_bands_and_track():
    rows = sm.serve_satellite_health([
        {"sat_key": "SAT-1", "date_key": "d", "health_score": 0.9},
        {"sat_key": "SAT-2", "date_key": "d", "health_score": 0.6},
        {"sat_key": "SAT-3", "date_key": "d", "health_score": 0.2},
    ])
    status = {r["sat_key"]: (r["status"], r["track"]) for r in rows}
    assert status["SAT-1"] == ("nominal", "sim")
    assert status["SAT-2"] == ("degraded", "sim")
    assert status["SAT-3"] == ("critical", "sim")


def test_launch_monthly_passthrough_marks_sim():
    rows = sm.serve_launch_monthly([
        {"provider_key": "P", "month_key": "2026-06", "launches": 4,
         "successes": 3, "success_rate": 0.75}])
    assert rows[0]["track"] == "sim"
    assert rows[0]["success_rate"] == 0.75


def test_weather_impact_storm_day_flag():
    rows = sm.serve_weather_impact([
        {"date_key": "d1", "max_kp_index": 6, "anomaly_rate": 0.3},
        {"date_key": "d2", "max_kp_index": 3, "anomaly_rate": 0.1},
    ])
    flags = {r["date_key"]: r["storm_day"] for r in rows}
    assert flags == {"d1": True, "d2": False}


def test_output_is_deterministically_sorted():
    vessels = [
        {"vessel_key": "V2", "date_key": "d"},
        {"vessel_key": "V1", "date_key": "d"},
    ]
    keys = [r["vessel_key"] for r in sm.serve_vessel_activity(vessels)]
    assert keys == ["V1", "V2"]
