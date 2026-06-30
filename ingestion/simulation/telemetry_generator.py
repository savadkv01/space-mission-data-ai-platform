"""Satellite telemetry generator.

Why synthetic data? Real public telemetry feeds are sparse, rate-limited, and
lack labelled anomalies. A controllable generator gives us: continuous high-rate
streams to exercise Kafka/back-pressure, realistic sensor physics, injectable
noise, and *labelled failure events* for downstream ML (anomaly detection).

The generator is deterministic given a ``seed`` so tests and demos are
reproducible. It emits records conforming to ``schemas.SATELLITE_TELEMETRY``.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterator, Optional


@dataclass
class SensorProfile:
    name: str
    baseline: float
    amplitude: float
    period_s: float
    noise_sigma: float
    unit: str


# Representative bus/payload sensors for a small EO satellite.
DEFAULT_SENSORS: list[SensorProfile] = [
    SensorProfile("battery_voltage", 28.0, 1.5, 5400, 0.15, "V"),
    SensorProfile("battery_temp_c", 18.0, 8.0, 5400, 0.4, "C"),
    SensorProfile("solar_panel_current", 4.5, 4.5, 5400, 0.2, "A"),
    SensorProfile("reaction_wheel_rpm", 3000.0, 400.0, 600, 25.0, "rpm"),
    SensorProfile("payload_temp_c", -5.0, 3.0, 5400, 0.3, "C"),
    SensorProfile("downlink_snr_db", 12.0, 2.0, 900, 0.5, "dB"),
]


@dataclass
class TelemetryGenerator:
    """Generates per-sensor telemetry samples for a fleet of satellites."""

    satellite_ids: list[str] = field(default_factory=lambda: ["SAT-001", "SAT-002", "SAT-003"])
    sensors: list[SensorProfile] = field(default_factory=lambda: list(DEFAULT_SENSORS))
    interval_s: float = 1.0
    seed: int = 42
    failure_rate: float = 0.002  # probability per sample of an injected anomaly
    start_time: Optional[datetime] = None  # fix for reproducible timestamps

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        self._t0 = self.start_time or datetime.now(timezone.utc)

    def _value(self, sensor: SensorProfile, elapsed_s: float, failing: bool) -> tuple[float, str]:
        phase = 2 * math.pi * (elapsed_s % sensor.period_s) / sensor.period_s
        value = sensor.baseline + sensor.amplitude * math.sin(phase)
        value += self._rng.gauss(0, sensor.noise_sigma)
        status = "NOMINAL"
        if failing:
            # Inject a physically-plausible fault signature.
            value += sensor.amplitude * self._rng.uniform(2.5, 5.0) * self._rng.choice([-1, 1])
            status = "ANOMALY"
        return round(value, 4), status

    def sample(self, satellite_id: str, step: int) -> dict:
        """Produce one telemetry record (all sensors) for a satellite."""
        elapsed = step * self.interval_s
        event_ts = (self._t0 + timedelta(seconds=elapsed)).isoformat()
        failing = self._rng.random() < self.failure_rate
        readings = {}
        worst = "NOMINAL"
        for sensor in self.sensors:
            val, status = self._value(sensor, elapsed, failing)
            readings[sensor.name] = {"value": val, "unit": sensor.unit, "status": status}
            if status == "ANOMALY":
                worst = "ANOMALY"
        return {
            "timestamp": event_ts,
            "satellite_id": satellite_id,
            "sensor_type": "bus_payload",
            "payload": readings,
            "metadata": {
                "generator": "synthetic",
                "schema_version": 1,
                "health": worst,
                "label_anomaly": failing,
            },
        }

    def stream(self, max_records: int | None = None) -> Iterator[dict]:
        """Yield telemetry records round-robin across the fleet.

        ``max_records=None`` streams indefinitely (for live producers); a finite
        value is used by demos and tests.
        """
        step = 0
        produced = 0
        while max_records is None or produced < max_records:
            for sat in self.satellite_ids:
                yield self.sample(sat, step)
                produced += 1
                if max_records is not None and produced >= max_records:
                    return
            step += 1
