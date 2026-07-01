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


@pytest.fixture
def fire_records() -> list[dict]:
    """Unwrapped FIRMS/VIIRS active-fire rows (CSV-shaped payload)."""
    rows = []
    for i in range(6):
        rows.append({
            "latitude": 24.0 + i * 0.1,
            "longitude": 54.0 + i * 0.1,
            "brightness": 320.0 + i,
            "acq_date": "2026-06-01",
            "acq_time": f"{100 + i:04d}",
            "satellite": "N",
            "instrument": "VIIRS",
            "confidence": "nominal" if i % 2 else "high",
            "frp": 12.5 + i,
            "daynight": "D",
            "_event_ts": "2026-06-01T01:00:00Z",
            "_source": "FIRMS",
            "_ingest_id": f"fire-{i}",
            "_batch_id": "batch-fire",
        })
    return rows


@pytest.fixture
def vessel_records() -> list[dict]:
    """Unwrapped GFW vessel-identity entries with a registryInfo block."""
    return [{
        "registryInfo": [{
            "ssvid": f"41000000{i}",
            "imo": f"92000{i}",
            "shipname": f"vessel-{i}",
            "flag": "are",
            "vesselType": "fishing",
            "transmissionDateFrom": "2026-01-01T00:00:00Z",
            "transmissionDateTo": f"2026-06-0{i + 1}T00:00:00Z",
        }],
        "_source": "GFW",
        "_ingest_id": f"gfw-{i}",
        "_batch_id": "batch-gfw",
    } for i in range(4)]


@pytest.fixture
def scene_records() -> list[dict]:
    """Unwrapped Sentinel Hub STAC scene features."""
    return [{
        "id": f"S2A_MSIL2A_2026060{i}",
        "collection": "sentinel-2-l2a",
        "bbox": [54.8, 24.8, 55.6, 25.5],
        "properties": {
            "datetime": f"2026-06-0{i + 1}T07:30:00Z",
            "platform": "sentinel-2a",
            "eo:cloud_cover": 5.0 * i,
        },
        "_source": "SENTINELHUB",
        "_ingest_id": f"scene-{i}",
        "_batch_id": "batch-scene",
    } for i in range(4)]
