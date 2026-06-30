# Telemetry Generator

Code: [telemetry_generator.py](telemetry_generator.py). Narrative: [docs/ingestion/06-simulation.md](../../docs/ingestion/06-simulation.md).

- Per-sensor model: `baseline + amplitude*sin(phase) + Gaussian noise`.
- Sensors: battery voltage/temp, solar current, reaction-wheel RPM, payload temp, downlink SNR.
- Fault injection (`failure_rate`) flags `status=ANOMALY` and `metadata.label_anomaly=true` for ML.
- Deterministic via `seed` (+ optional `start_time`); emits `satellite_telemetry` schema.
- Output keyed by `satellite_id` for partition-stable streaming.
