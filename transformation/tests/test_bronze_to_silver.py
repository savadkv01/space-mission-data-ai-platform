from __future__ import annotations

from transformation.batch.bronze_to_silver import (
    silver_orbit,
    silver_space_weather,
    silver_telemetry,
)


def test_silver_telemetry_flattens_and_labels(telemetry_records):
    result = silver_telemetry(telemetry_records)
    assert result.rows, "expected conformed telemetry rows"
    row = result.rows[0]
    assert "battery_voltage_value" in row
    assert "battery_voltage_status" in row
    assert row["event_ts"].endswith("+00:00")
    # at least one labelled anomaly present in the fixture
    assert any(r["label_anomaly"] for r in result.rows)
    # anomaly_sensor_count counts ANOMALY-status sensors
    assert all(r["anomaly_sensor_count"] >= 0 for r in result.rows)


def test_silver_telemetry_rejects_missing_keys():
    bad = [{"timestamp": "2026-06-01T00:00:00Z"}]  # no satellite_id
    result = silver_telemetry(bad)
    assert not result.rows
    assert result.quarantine and "null:satellite_id" in result.quarantine[0]["_reasons"]


def test_silver_orbit_normalizes_geo(orbit_records):
    result = silver_orbit(orbit_records)
    assert result.rows
    row = result.rows[0]
    assert "geo_key" in row and "grid_lat" in row
    assert -180 <= row["longitude"] < 180


def test_silver_orbit_rejects_out_of_range():
    bad = [{"timestamp": "2026-06-01T00:00:00Z", "satellite_id": "S1",
            "latitude": 999, "longitude": 0}]
    result = silver_orbit(bad)
    assert not result.rows
    assert "range:latitude" in result.quarantine[0]["_reasons"]


def test_silver_space_weather(space_weather_records):
    result = silver_space_weather(space_weather_records)
    assert result.rows
    assert all(0 <= r["kp_index"] <= 9 for r in result.rows)
    assert all(r["flare_letter"] in {"A", "B", "C", "M", "X"} for r in result.rows)


def test_silver_dedup_removes_duplicate_event(space_weather_records):
    dupes = space_weather_records + space_weather_records  # duplicate event times
    result = silver_space_weather(dupes)
    keys = {(r["event_ts"], r["event_type"]) for r in result.rows}
    assert len(keys) == len(result.rows)
