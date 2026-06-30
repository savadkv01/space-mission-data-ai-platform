# Topic Architecture

Defined centrally in [config/settings.py](../config/settings.py) (`KafkaSettings`).

| Topic | Partitions | Key | Purpose |
| --- | --- | --- | --- |
| `telemetry.satellite.raw` | 3 | satellite_id | raw telemetry intake |
| `telemetry.satellite.cleaned` | 3 | satellite_id | validated telemetry |
| `telemetry.satellite.dlq` | 1 | satellite_id | rejected records |
| `space.weather.events` | 1 | time_tag | Kp / flare events |
| `launch.events` | 1 | — | launch schedule events |
| `orbit.position.stream` | 3 | norad id | orbit positions / GP sets |

## Partitioning
- Key = `satellite_id` preserves per-satellite ordering and spreads load.
- Partition count bounds consumer-group parallelism (increase before scaling consumers).

Narrative: [docs/ingestion/02-streaming-design.md](../../docs/ingestion/02-streaming-design.md) · scaling: [docs/ingestion/13-scalability.md](../../docs/ingestion/13-scalability.md).
