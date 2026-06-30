from datetime import datetime, timezone

from ingestion.simulation.orbit_simulator import OrbitSimulator
from ingestion.simulation.space_weather_generator import SpaceWeatherGenerator
from ingestion.simulation.telemetry_generator import TelemetryGenerator

_FIXED_T0 = datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_telemetry_is_deterministic_with_seed():
    a = list(TelemetryGenerator(seed=1, start_time=_FIXED_T0).stream(max_records=10))
    b = list(TelemetryGenerator(seed=1, start_time=_FIXED_T0).stream(max_records=10))
    assert a == b


def test_telemetry_record_shape():
    rec = next(iter(TelemetryGenerator().stream(max_records=1)))
    assert {"timestamp", "satellite_id", "sensor_type", "payload", "metadata"} <= rec.keys()
    assert isinstance(rec["payload"], dict) and rec["payload"]


def test_orbit_positions_within_bounds():
    for rec in OrbitSimulator(interval_s=60).stream(max_records=20):
        assert -90 <= rec["latitude"] <= 90
        assert -180 <= rec["longitude"] <= 180
        assert rec["altitude_km"] > 0


def test_space_weather_kp_range():
    for rec in SpaceWeatherGenerator().stream(max_records=20):
        assert 0.0 <= rec["kp_index"] <= 9.0
        assert rec["flare_class"][0] in {"A", "B", "C", "M", "X"}
