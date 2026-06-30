from ingestion.quality.validators import DuplicateTracker, validate_record


def test_valid_telemetry_passes():
    record = {
        "timestamp": "2024-06-01T00:00:00Z",
        "satellite_id": "SAT-001",
        "sensor_type": "bus_payload",
        "payload": {"battery_voltage": {"value": 28.0}},
    }
    outcome = validate_record(record, schema="satellite_telemetry")
    assert outcome.valid, outcome.errors


def test_missing_required_field_fails():
    record = {"timestamp": "2024-06-01T00:00:00Z", "sensor_type": "x", "payload": {}}
    outcome = validate_record(record, schema="satellite_telemetry")
    assert not outcome.valid
    assert any("satellite_id" in e for e in outcome.errors)


def test_geospatial_out_of_range_fails():
    record = {"timestamp": "2024-06-01T00:00:00Z", "latitude": 120.0, "longitude": 10.0}
    outcome = validate_record(record)
    assert not outcome.valid
    assert "geospatial" in outcome.rule_hits


def test_bad_timestamp_fails():
    record = {"timestamp": "not-a-date", "satellite_id": "S", "sensor_type": "x", "payload": {}}
    outcome = validate_record(record, schema="satellite_telemetry")
    assert not outcome.valid
    assert "timestamp" in outcome.rule_hits


def test_duplicate_detection():
    dedup = DuplicateTracker()
    rec = {"timestamp": "2024-06-01T00:00:00Z"}
    first = validate_record(rec, checksum="abc", dedup=dedup)
    second = validate_record(rec, checksum="abc", dedup=dedup)
    assert first.valid
    assert not second.valid and "duplicate" in second.rule_hits
