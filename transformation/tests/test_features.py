from __future__ import annotations

from transformation.batch.bronze_to_silver import (
    silver_orbit,
    silver_space_weather,
    silver_telemetry,
)
from transformation.features.feature_engineering import (
    orbit_features,
    satellite_health_features,
    space_weather_features,
)


def test_satellite_health_features(telemetry_records):
    silver = silver_telemetry(telemetry_records).rows
    feats = satellite_health_features(silver)
    assert feats
    f = feats[0]
    assert {"entity_id", "event_ts", "signal_stability", "sensor_drift",
            "anomaly_indicator"} <= set(f)
    assert all(0.0 <= x["signal_stability"] <= 1.0 for x in feats)
    assert all(x["anomaly_indicator"] in (0, 1) for x in feats)


def test_orbit_features(orbit_records):
    silver = silver_orbit(orbit_records).rows
    feats = orbit_features(silver)
    assert feats
    assert all(x["ground_speed_kmps"] >= 0 for x in feats)
    assert all(0.0 < x["trajectory_stability"] <= 1.0 for x in feats)


def test_space_weather_features(space_weather_records):
    silver = silver_space_weather(space_weather_records).rows
    feats = space_weather_features(silver)
    assert feats
    for x in feats:
        assert 0.0 <= x["solar_storm_intensity"] <= 1.0
        assert 0.0 <= x["radiation_exposure_index"] <= 1.0
        assert x["is_storm"] in (0, 1)
