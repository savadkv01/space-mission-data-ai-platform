# Kafka Design (Streaming)

Component design for the Kafka streaming layer. Full narrative: [docs/ingestion/02-streaming-design.md](../../docs/ingestion/02-streaming-design.md).

## Code
- IO factory: [common/kafka_io.py](../common/kafka_io.py)
- Settings (bootstrap, topics): [config/settings.py](../config/settings.py)
- Topic creation: [scripts/create_topics.py](../scripts/create_topics.py)

## Key decisions
- Single-broker KRaft (no ZooKeeper), repl factor 1 — laptop-sized.
- Idempotent producers (`acks=all`, `enable_idempotence`), gzip, `linger_ms=50`.
- Consumers: manual offset commit → at-least-once.
- DLQ topic for poison/invalid messages.

See [topic-architecture.md](topic-architecture.md) and [producer-consumer-design.md](producer-consumer-design.md).
