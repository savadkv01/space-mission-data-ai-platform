# 13 — Simulation Sources (Synthetic Telemetry, Orbit, Space Weather)

> **These sources are synthetic by design** (ADR-09 simulation track). They exist because real
> spacecraft telemetry is proprietary and has no labelled anomalies. Never present their values as
> real-world observations.

## 1. Identity Card

| Bronze `_source` (envelope) | Bronze folder(s) | Generator | Transport | Silver entity |
| --- | --- | --- | --- | --- |
| `TELEMETRY` | `telemetry/` (stream), `satellite_telemetry/` (seed) | [`telemetry_generator.py`](../../../ingestion/simulation/telemetry_generator.py) | Kafka `telemetry.satellite.raw` → [`raw_ingest_consumer`](../../../ingestion/streaming/consumers/raw_ingest_consumer.py) → MinIO | `silver_telemetry` |
| `ORBIT` | `orbit_position/` | [`orbit_simulator.py`](../../../ingestion/simulation/orbit_simulator.py) | Kafka `orbit.position.stream` / seed file | `silver_orbit` |
| `SPACE_WEATHER` | `space_weather/` | [`space_weather_generator.py`](../../../ingestion/simulation/space_weather_generator.py) | Kafka `space.weather.events` / seed file | `silver_space_weather` (**unioned with real `SWPC`**) |

Seed files for offline demos live in [`.bronze_seed/`](../../../.bronze_seed/).

## 2. Why Synthetic?

| Need | Real-data problem | Synthetic answer |
| --- | --- | --- |
| Continuous high-rate stream to exercise Kafka, back-pressure and the DLQ | Public feeds are sparse and rate-limited | 1 Hz per sensor per satellite, configurable |
| **Labelled anomalies** for ML | Real anomalies are rare and unlabelled | `failure_rate` injects faults with `label_anomaly = true` |
| Reproducibility | Live data changes | Deterministic given `seed` |

## 3. How the Data Is Generated

### 3.1 Telemetry

Each sensor follows `baseline + amplitude · sin(2π·t/period) + Gaussian noise`, mimicking orbital
day/night cycles (period 5,400 s ≈ one 90-minute LEO orbit). With probability `failure_rate`
(default 0.002 per sample), values are pushed out of range and flagged `ANOMALY`.

| Sensor | Baseline | Amplitude | Period | Unit | Physical meaning |
| --- | --- | --- | --- | --- | --- |
| `battery_voltage` | 28.0 | 1.5 | 5,400 s | V | 28 V bus typical of small satellites; dips in eclipse |
| `battery_temp_c` | 18.0 | 8.0 | 5,400 s | °C | Thermal cycling between sun and eclipse |
| `solar_panel_current` | 4.5 | 4.5 | 5,400 s | A | ~0 in eclipse, max in sunlight |
| `reaction_wheel_rpm` | 3,000 | 400 | 600 s | rpm | Attitude-control momentum wheel |
| `payload_temp_c` | −5.0 | 3.0 | 5,400 s | °C | Cooled instrument |
| `downlink_snr_db` | 12.0 | 2.0 | 900 s | dB | Ground-station pass signal quality |

Real Bronze record (anomalous sample):

```json
{"_source": "TELEMETRY", "payload": {"timestamp": "2026-11-14T17:58:02.514018+00:00",
  "satellite_id": "SAT-002", "sensor_type": "bus_payload",
  "payload": {"battery_voltage": {"value": 34.6394, "unit": "V", "status": "ANOMALY"},
              "solar_panel_current": {"value": -7.6187, "unit": "A", "status": "ANOMALY"}, "…": "…"},
  "metadata": {"generator": "synthetic", "schema_version": 1, "health": "ANOMALY", "label_anomaly": true}}}
```

Note the **double `payload`**: the envelope's `payload` wraps a telemetry message whose own
`payload` holds the sensor readings.

### 3.2 Orbit positions

SGP4 propagation of built-in TLEs (`ISS`, `SAT-A`, 2024 epoch; README SG-07) produces
sub-satellite latitude, longitude and altitude every `interval_s` (default 10 s). If `sgp4` is not
installed, an analytic circular-orbit fallback is used, and `propagator` records which method was
applied.

```json
{"timestamp": "2026-07-13T11:32:36.769161+00:00", "satellite_id": "ISS",
 "latitude": 14.59785, "longitude": -137.93719, "altitude_km": 384.132, "propagator": "sgp4"}
```

### 3.3 Space weather

`kp_index ~ N(3.0, 1.5)` clipped to 0–9; flare class drawn from A/B/C/M/X with weights
40/35/18/6/1; `geomagnetic_storm = kp ≥ 5`.

```json
{"timestamp": "…", "event_type": "space_weather", "kp_index": 2.6, "flare_class": "B2",
 "geomagnetic_storm": false, "severity": "quiet", "source": "synthetic"}
```

## 4. Field Dictionary (key fields)

| Field | Source | Meaning |
| --- | --- | --- |
| `satellite_id` | Telemetry, orbit | `SAT-001…003` (telemetry), `ISS`/`SAT-A` (orbit) |
| `payload.<sensor>.value/unit/status` | Telemetry | Reading, unit, `NOMINAL`/`ANOMALY` |
| `metadata.health` | Telemetry | Worst status across sensors |
| `metadata.label_anomaly` | Telemetry | **Ground-truth ML label** |
| `altitude_km` | Orbit | Height above a spherical Earth (6,371 km radius) |
| `propagator` | Orbit | `sgp4` or `analytic` |
| `kp_index`, `flare_class`, `geomagnetic_storm`, `severity` | Space weather | Synthetic space-weather state |
| `source = "synthetic"` | Space weather | Distinguishes synthetic from real SWPC rows |

## 5. How to Read & Interpret

- Use telemetry for **pipeline and ML demonstration** (anomaly detection, streaming windows such
  as `stream_sat_health_1m`), never for spacecraft-engineering conclusions.
- **Mixed real and synthetic Kp:** `silver_space_weather` unions real `SWPC` with synthetic
  `space_weather`. Filter on `_source` (`SWPC` vs `SPACE_WEATHER`) or `source = 'synthetic'` before
  any statistic.
- Synthetic Kp has a mean of 3 and **G1+ storms ~9 % of the time**, far more often than reality.

## 6. Quality, Limitations & Gotchas

| Gotcha | Mitigation |
| --- | --- |
| Synthetic distributions ≠ reality | Label dashboards "Simulation"; keep ADR-09 boundaries |
| Stale TLE seeds | Seed from Bronze `CELESTRAK` (SG-07) |
| Spherical-Earth altitude and approximate GMST | Adequate for ground tracks; not for conjunction analysis |
| Two Bronze folders for telemetry (`telemetry/`, `satellite_telemetry/`) | Stream vs seed; dedupe on (`satellite_id`, `timestamp`) |

## 7. Downstream Lineage

`TELEMETRY` → `silver_telemetry` → `fact_sat_health`, `stream_sat_health_1m` →
`serving_sat_health` · `ORBIT` → `silver_orbit` → `orbit_trajectory` · `SPACE_WEATHER` + `SWPC` →
`silver_space_weather` → `fact_weather_impact` → Simulation-Track dashboard.

## 8. References

- Generator docs: [`telemetry-generator.md`](../../../ingestion/simulation/telemetry-generator.md), [`orbit-simulator.md`](../../../ingestion/simulation/orbit-simulator.md)
- ADR-09 (simulation track): [docs/data-modeling/17-adr.md](../../data-modeling/17-adr.md)
