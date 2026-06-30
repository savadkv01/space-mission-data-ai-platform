# Feature Definitions

> Code: [feature_engineering.py](feature_engineering.py)

Keys on every row: `entity_id`, `event_ts`, `feature_namespace`.

## sat_health

| Feature | Type | Definition | Range |
| --- | --- | --- | --- |
| `signal_stability` | float | `1 / (1 + stddev(downlink_snr over window))` | (0, 1] |
| `sensor_drift` | float | Δ rolling-mean battery voltage over window | ℝ |
| `anomaly_indicator` | int | 1 if any sensor `status = ANOMALY` | {0,1} |
| `anomaly_sensor_count` | int | # sensors in ANOMALY | ≥0 |

## orbit

| Feature | Type | Definition | Range |
| --- | --- | --- | --- |
| `ground_speed_kmps` | float | haversine distance ÷ Δt between samples | ≥0 |
| `velocity_variance` | float | trailing variance of ground speed | ≥0 |
| `orbit_deviation` | float | |altitude − rolling-mean altitude| | ≥0 |
| `trajectory_stability` | float | `1 / (1 + velocity_variance)` | (0, 1] |

## space_weather

| Feature | Type | Definition | Range |
| --- | --- | --- | --- |
| `kp_normalized` | float | `kp_index / 9` | [0, 1] |
| `flare_energy_class` | int | A=1 … X=5 | [1, 5] |
| `solar_storm_intensity` | float | `kp_normalized × (flare_energy / 5)` | [0, 1] |
| `radiation_exposure_index` | float | `0.6·kp_normalized + 0.4·(flare_energy/5)` | [0, 1] |
| `is_storm` | int | 1 if geomagnetic storm | {0,1} |

## Consuming models (Phase 10+)

| Model | Features |
| --- | --- |
| Satellite anomaly detection | sat_health.* |
| Orbit decay / station-keeping | orbit.* |
| Space-weather impact / alerting | space_weather.* + sat_health.anomaly_indicator |
