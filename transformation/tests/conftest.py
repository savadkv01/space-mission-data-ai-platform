"""Shared fixtures: synthetic Bronze-unwrapped records for the transforms."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

BASE = datetime(2026, 6, 1, tzinfo=timezone.utc)


@pytest.fixture
def telemetry_records() -> list[dict]:
    rows = []
    for i in range(20):
        anomaly = i % 7 == 0
        rows.append({
            "timestamp": (BASE + timedelta(seconds=i)).isoformat(),
            "satellite_id": f"SAT-00{i % 2 + 1}",
            "sensor_type": "bus_payload",
            "battery_voltage_value": None,  # provided via payload below
            "payload": {
                "battery_voltage": {"value": 28.0 + (i % 4) * 0.2, "unit": "V",
                                    "status": "ANOMALY" if anomaly else "NOMINAL"},
                "downlink_snr_db": {"value": 12.0 + (i % 3), "unit": "dB", "status": "NOMINAL"},
            },
            "metadata": {"health": "ANOMALY" if anomaly else "NOMINAL",
                         "label_anomaly": anomaly},
            "_ingest_id": f"ing-{i}",
            "_batch_id": "batch-1",
        })
    # Flatten payload like unwrap would not — transform reads payload directly.
    for r in rows:
        r.pop("battery_voltage_value", None)
    return rows


@pytest.fixture
def orbit_records() -> list[dict]:
    return [{
        "timestamp": (BASE + timedelta(seconds=i * 30)).isoformat(),
        "satellite_id": "SAT-001",
        "latitude": (i * 5) % 80,
        "longitude": ((i * 13) % 360) - 180,
        "altitude_km": 420.0 + (i % 3),
    } for i in range(10)]


@pytest.fixture
def space_weather_records() -> list[dict]:
    return [{
        "timestamp": (BASE + timedelta(minutes=i)).isoformat(),
        "event_type": "space_weather",
        "kp_index": float(i % 9),
        "flare_class": "M3" if i % 4 == 0 else "B2",
        "geomagnetic_storm": (i % 9) >= 5,
        "severity": "G1+" if (i % 9) >= 5 else "quiet",
        "source": "synthetic",
    } for i in range(12)]
