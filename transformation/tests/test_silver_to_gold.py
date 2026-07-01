from __future__ import annotations

from transformation.batch.bronze_to_silver import (
    silver_scene,
    silver_space_weather,
    silver_telemetry,
    silver_vessel,
)
from transformation.batch.silver_to_gold import (
    gold_aoi_validation,
    gold_earth_observation,
    gold_flood_aoi,
    gold_launch_performance,
    gold_satellite_health,
    gold_scene_catalog,
    gold_space_weather_impact,
    gold_vessel_activity,
    gold_wildfire_aoi,
)


def test_gold_satellite_health_grain(telemetry_records):
    silver = silver_telemetry(telemetry_records).rows
    gold = gold_satellite_health(silver)
    # one row per (sat, day)
    keys = {(r["sat_key"], r["date_key"]) for r in gold}
    assert len(keys) == len(gold)
    for r in gold:
        assert 0.0 <= r["health_score"] <= 1.0
        assert 0.0 <= r["anomaly_density"] <= 1.0


def test_gold_space_weather_impact(telemetry_records, space_weather_records):
    s_tel = silver_telemetry(telemetry_records).rows
    s_wea = silver_space_weather(space_weather_records).rows
    gold = gold_space_weather_impact(s_wea, s_tel)
    assert gold
    for r in gold:
        if r["anomaly_rate"] is not None:
            assert 0.0 <= r["anomaly_rate"] <= 1.0


def test_gold_launch_performance():
    launches = [
        {"event_ts": "2026-06-01T00:00:00+00:00", "provider": "P1", "success": True, "delay_days": 2},
        {"event_ts": "2026-06-15T00:00:00+00:00", "provider": "P1", "success": False, "delay_days": 5},
    ]
    gold = gold_launch_performance(launches)
    assert len(gold) == 1
    assert gold[0]["launches"] == 2
    assert gold[0]["success_rate"] == 0.5
    assert gold[0]["mean_delay_days"] == 3.5


def test_gold_earth_observation():
    fires = [
        {"event_ts": "2026-06-01T00:00:00+00:00", "geo_key": "10.0:20.0", "frp": 30},
        {"event_ts": "2026-06-01T01:00:00+00:00", "geo_key": "10.0:20.0", "frp": 50},
    ]
    gold = gold_earth_observation(fires)
    assert len(gold) == 1
    assert gold[0]["detections"] == 2
    assert gold[0]["max_frp"] == 50.0
    assert gold[0]["median_frp"] == 40.0


def test_gold_vessel_activity_grain(vessel_records):
    silver = silver_vessel(vessel_records).rows
    gold = gold_vessel_activity(silver)
    assert gold
    keys = {(r["vessel_key"], r["date_key"]) for r in gold}
    assert len(keys) == len(gold)
    for r in gold:
        assert r["transmissions"] >= 1
        assert isinstance(r["suspicious_flag"], bool)


def test_gold_scene_catalog_is_searchable(scene_records):
    silver = silver_scene(scene_records).rows
    gold = gold_scene_catalog(silver)
    assert gold
    keys = {r["scene_key"] for r in gold}
    assert len(keys) == len(gold)  # 1 row per scene
    assert all(r["is_searchable"] for r in gold)
    assert all(0.0 <= r["completeness_score"] <= 1.0 for r in gold)


# --- Per-AOI marts (Action 3 geospatial joins) ------------------------------

_FIRE_AOI = {"aoi_key": "EMSR200", "event_type": "fire",
             "bbox": [54.8, 24.8, 55.6, 25.5],
             "polygons": [[[[54.8, 24.8], [55.6, 24.8], [55.6, 25.5],
                            [54.8, 25.5], [54.8, 24.8]]]]}
_FLOOD_AOI = {"aoi_key": "EMSR100", "event_type": "flood", "area_km2": 4200.0,
              "event_date": "2026-06-10T00:00:00Z",
              "bbox": [54.8, 24.8, 55.6, 25.5],
              "polygons": [[[[54.8, 24.8], [55.6, 24.8], [55.6, 25.5],
                             [54.8, 25.5], [54.8, 24.8]]]]}


def test_gold_wildfire_aoi_point_in_polygon():
    fires = [
        {"event_ts": "2026-06-11T00:00:00+00:00", "latitude": 25.0, "longitude": 55.0, "frp": 30},
        {"event_ts": "2026-06-11T01:00:00+00:00", "latitude": 25.1, "longitude": 55.1, "frp": 50},
        {"event_ts": "2026-06-11T02:00:00+00:00", "latitude": 10.0, "longitude": 10.0, "frp": 99},
    ]
    gold = gold_wildfire_aoi(fires, [_FIRE_AOI])
    assert len(gold) == 1  # only the two in-polygon detections attribute
    assert gold[0]["aoi_key"] == "EMSR200"
    assert gold[0]["detections"] == 2
    assert gold[0]["max_frp"] == 50.0


def test_gold_flood_aoi_from_ndwi():
    index_rows = [
        {"index_name": "NDWI", "event_ts": "2026-06-10T00:00:00+00:00",
         "bbox": "54.8,24.8,55.6,25.5", "mean": 0.3, "valid_pixel_fraction": 0.9},
        {"index_name": "NDVI", "event_ts": "2026-06-10T00:00:00+00:00",
         "bbox": "54.8,24.8,55.6,25.5", "mean": 0.6, "valid_pixel_fraction": 0.9},
    ]
    gold = gold_flood_aoi(index_rows, [_FLOOD_AOI])
    assert len(gold) == 1
    assert gold[0]["aoi_key"] == "EMSR100"
    assert gold[0]["flood_flag"] is True  # NDWI mean 0.3 > 0
    assert gold[0]["ndwi_mean"] == 0.3


def test_gold_aoi_validation_corroborates():
    wildfire = [{"aoi_key": "EMSR200", "date_key": "2026-06-11", "detections": 2}]
    flood = [{"aoi_key": "EMSR100", "date_key": "2026-06-10", "flood_flag": True}]
    gold = gold_aoi_validation([_FIRE_AOI, _FLOOD_AOI], wildfire, flood)
    by = {r["aoi_key"]: r for r in gold}
    assert by["EMSR200"]["corroborated"] is True
    assert by["EMSR100"]["corroborated"] is True
    assert by["EMSR100"]["event_type"] == "flood"


def test_gold_aoi_validation_uncorroborated_when_no_evidence():
    gold = gold_aoi_validation([_FIRE_AOI], [], [])
    assert gold[0]["corroborated"] is False
    assert gold[0]["evidence_days"] == 0
