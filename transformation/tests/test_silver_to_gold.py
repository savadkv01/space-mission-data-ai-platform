from __future__ import annotations

from transformation.batch.bronze_to_silver import (
    silver_space_weather,
    silver_telemetry,
)
from transformation.batch.silver_to_gold import (
    gold_earth_observation,
    gold_launch_performance,
    gold_satellite_health,
    gold_space_weather_impact,
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
