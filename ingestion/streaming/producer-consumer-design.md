# Producer / Consumer Design

## Producers
| Producer | Source → Topic | Code |
| --- | --- | --- |
| Telemetry | synthetic → `telemetry.satellite.raw` | [producers/telemetry_producer.py](producers/telemetry_producer.py) |
| API bridge | SWPC/CelesTrak → events/orbit | [producers/api_bridge_producer.py](producers/api_bridge_producer.py) |

## Consumers
| Consumer | Role | Code |
| --- | --- | --- |
| Raw writer | Kafka → Bronze (MinIO) | [consumers/raw_ingest_consumer.py](consumers/raw_ingest_consumer.py) |
| Validation | raw → cleaned / DLQ | [consumers/validation_consumer.py](consumers/validation_consumer.py) |

## Delivery
- `enable_auto_commit=False`; commit only after durable write/route → at-least-once.
- Idempotent producers avoid duplicate writes on retry; `_checksum` dedup at validation.

Narrative: [docs/ingestion/02-streaming-design.md](../../docs/ingestion/02-streaming-design.md).
