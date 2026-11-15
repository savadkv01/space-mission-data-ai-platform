import json
from datetime import datetime, timezone

from ingestion.quality.validators import validate_record
from ingestion.simulation.telemetry_generator import TelemetryGenerator
from transformation.streaming.spark_streaming import extract_stream_fields

_T0 = datetime(2026, 6, 1, tzinfo=timezone.utc)


def test_generator_anomaly_labels_survive_validation_and_parsing():
    generator = TelemetryGenerator(seed=7, start_time=_T0, failure_rate=1.0)
    records = list(generator.stream(max_records=6))

    parsed = []
    for record in records:
        assert validate_record(record, schema="satellite_telemetry").valid
        # The validation consumer forwards the record unchanged through Kafka JSON.
        parsed.append(extract_stream_fields(json.loads(json.dumps(record))))

    assert [p["label_anomaly"] for p in parsed] == [True] * 6
    assert {p["health"] for p in parsed} == {"ANOMALY"}
    assert [p["satellite_id"] for p in parsed] == [r["satellite_id"] for r in records]


def test_nominal_generator_records_parse_as_not_anomalous():
    records = TelemetryGenerator(seed=7, start_time=_T0, failure_rate=0.0).stream(max_records=3)
    assert all(extract_stream_fields(r)["label_anomaly"] is False for r in records)


def test_flat_demo_records_fall_back_to_root_fields():
    record = {"timestamp": "2026-06-01T12:00:30", "satellite_id": "SAT-001",
              "sensor_type": "thermal", "health": "NOMINAL", "label_anomaly": True}
    assert extract_stream_fields(record)["label_anomaly"] is True
    assert extract_stream_fields(record)["health"] == "NOMINAL"
