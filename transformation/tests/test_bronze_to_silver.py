from __future__ import annotations

from transformation.batch.bronze_to_silver import (
    clean_fire,
    silver_orbit,
    silver_space_weather,
    silver_telemetry,
)


def test_fire_preserves_viirs_channel_temperature_and_provenance():
    row = clean_fire({"latitude": 25, "longitude": 55, "acq_date": "2026-10-31",
                      "acq_time": "1100", "instrument": "VIIRS", "bright_ti4": "330.2",
                      "bright_ti5": "290.1", "frp": "12.5", "confidence": "n",
                      "_ingest_id": "id", "_batch_id": "batch"}).record
    assert row is not None
    assert row["brightness"] == 330.2 and row["brightness_unit"] == "K"
    assert row["brightness_source_field"] == "bright_ti4"
    assert row["brightness_status"] == "present"
    assert row["bright_ti5"] == 290.1
    assert row["frp"] == 12.5 and row["confidence"] == 66
    assert row["_ingest_id"] == "id" and row["_batch_id"] == "batch"


def test_fire_modis_missing_and_invalid_brightness_are_distinct():
    base = {"latitude": 25, "longitude": 55, "acq_date": "2026-10-31",
            "instrument": "MODIS", "bright_ti4": "330", "bright_t31": "290"}
    missing = clean_fire(base).record
    invalid = clean_fire({**base, "brightness": "invalid"}).record
    present = clean_fire({**base, "brightness": "335"}).record
    assert missing is not None and invalid is not None and present is not None
    assert missing["brightness"] is None and missing["brightness_status"] == "source_absent"
    assert invalid["brightness"] is None and invalid["brightness_status"] == "source_invalid"
    assert present["brightness"] == 335 and present["brightness_source_field"] == "brightness"
    assert present["bright_t31"] == 290
    nonfinite = clean_fire({**base, "brightness": "NaN"}).record
    assert nonfinite is not None
    assert nonfinite["brightness"] is None and nonfinite["brightness_status"] == "source_invalid"


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
