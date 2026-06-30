"""AI feature engineering layer (Task 8).

Features are derived from Silver (not Bronze) so they inherit cleaning + dedup,
and they are *reused* across models by writing them to a feature dataset keyed by
``(entity_id, event_ts)``. Derivation is windowed and deterministic so the same
feature can be recomputed for training and serving (no train/serve skew).

Feature families:
- Satellite health: signal stability, anomaly indicators, sensor drift
- Orbit analytics: orbit deviation, velocity variance, trajectory stability
- Space weather: solar-storm intensity, radiation exposure index
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from transformation.geospatial.spatial_transform import haversine_km
from transformation.timeseries.time_series import parse_ts, rolling_mean

_FLARE_ENERGY = {"A": 1, "B": 2, "C": 3, "M": 4, "X": 5}


def _stddev(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    return math.sqrt(var)


# --- Satellite health features ---------------------------------------------

def satellite_health_features(silver_telemetry: list[dict[str, Any]],
                              window: int = 10) -> list[dict[str, Any]]:
    """Per-sample features over a trailing window, grouped per satellite.

    - signal_stability: inverse of rolling SNR volatility (higher = steadier)
    - sensor_drift: trailing change in battery voltage rolling mean
    - anomaly_indicator: 1 if any sensor reports ANOMALY this sample
    """
    by_sat: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in silver_telemetry:
        sat = r.get("satellite_id")
        if sat and parse_ts(r.get("event_ts")):
            by_sat[sat].append(r)

    out: list[dict[str, Any]] = []
    for sat, rows in by_sat.items():
        rows.sort(key=lambda r: r["event_ts"])
        snr = [r.get("downlink_snr_db_value") or 0.0 for r in rows]
        volt = [r.get("battery_voltage_value") or 0.0 for r in rows]
        volt_rm = rolling_mean(volt, window)
        for i, r in enumerate(rows):
            w0 = max(0, i - window + 1)
            snr_window = snr[w0:i + 1]
            stability = 1.0 / (1.0 + _stddev(snr_window))
            drift = round(volt_rm[i] - volt_rm[w0], 4)
            out.append({
                "entity_id": sat,
                "event_ts": r["event_ts"],
                "feature_namespace": "sat_health",
                "signal_stability": round(stability, 4),
                "sensor_drift": drift,
                "anomaly_indicator": 1 if r.get("anomaly_sensor_count", 0) > 0 else 0,
                "anomaly_sensor_count": r.get("anomaly_sensor_count", 0),
            })
    return out


# --- Orbit analytics features ----------------------------------------------

def orbit_features(silver_orbit: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per-step orbit features from consecutive ground-track points.

    - ground_speed_kmps: great-circle distance / dt between samples
    - velocity_variance: trailing variance of ground speed
    - orbit_deviation: |altitude - rolling mean altitude|
    - trajectory_stability: inverse of recent speed variance
    """
    by_sat: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in silver_orbit:
        sat = r.get("satellite_id")
        if sat and parse_ts(r.get("event_ts")):
            by_sat[sat].append(r)

    out: list[dict[str, Any]] = []
    for sat, rows in by_sat.items():
        rows.sort(key=lambda r: r["event_ts"])
        alts = [r.get("altitude_km") or 0.0 for r in rows]
        alt_rm = rolling_mean(alts, 5)
        speeds: list[float] = [0.0]
        for prev, cur in zip(rows, rows[1:]):
            dt = (parse_ts(cur["event_ts"]) - parse_ts(prev["event_ts"])).total_seconds()  # type: ignore[union-attr]
            dist = haversine_km(prev["latitude"], prev["longitude"],
                                cur["latitude"], cur["longitude"])
            speeds.append(round(dist / dt, 4) if dt > 0 else 0.0)
        for i, r in enumerate(rows):
            w0 = max(0, i - 5 + 1)
            recent = speeds[w0:i + 1]
            var = round(_stddev(recent) ** 2, 6)
            out.append({
                "entity_id": sat,
                "event_ts": r["event_ts"],
                "feature_namespace": "orbit",
                "ground_speed_kmps": speeds[i],
                "velocity_variance": var,
                "orbit_deviation": round(abs((r.get("altitude_km") or 0.0) - alt_rm[i]), 4),
                "trajectory_stability": round(1.0 / (1.0 + var), 4),
            })
    return out


# --- Space weather features -------------------------------------------------

def space_weather_features(silver_space_weather: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per-event space-weather features.

    - solar_storm_intensity: normalized Kp (0-1) scaled by flare energy class
    - radiation_exposure_index: composite of Kp and flare energy
    """
    out: list[dict[str, Any]] = []
    for r in silver_space_weather:
        if not parse_ts(r.get("event_ts")):
            continue
        kp = float(r.get("kp_index", 0.0))
        flare_letter = str(r.get("flare_letter") or str(r.get("flare_class", "A"))[:1]).upper()
        energy = _FLARE_ENERGY.get(flare_letter, 1)
        kp_norm = kp / 9.0
        intensity = round(kp_norm * (energy / 5.0), 4)
        radiation = round(0.6 * kp_norm + 0.4 * (energy / 5.0), 4)
        out.append({
            "entity_id": "GLOBAL",
            "event_ts": r["event_ts"],
            "feature_namespace": "space_weather",
            "kp_normalized": round(kp_norm, 4),
            "flare_energy_class": energy,
            "solar_storm_intensity": intensity,
            "radiation_exposure_index": radiation,
            "is_storm": 1 if r.get("geomagnetic_storm") else 0,
        })
    return out
