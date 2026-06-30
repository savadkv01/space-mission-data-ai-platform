# 15 - Trade-off Analysis

> **Phase 8 - Data Ingestion** · Document 15 of 17

## Purpose

Document the key ingestion design trade-offs, alternatives considered, and rationale.

## Streaming vs Batch

| Aspect | Streaming (Kafka) | Batch (Airflow) |
| --- | --- | --- |
| Latency | seconds | minutes–daily |
| Complexity | higher | lower |
| Best for | telemetry, events | archives, imagery metadata |
| **Decision** | hybrid — use each where it fits | |

## Kafka vs Simpler Queue (e.g. Redis/RabbitMQ)

- **Chosen: Kafka.** Replayable log, partitioned parallelism, consumer groups, DLQ, ecosystem fit.
- Trade-off: heavier than a simple queue; mitigated by single-broker KRaft (no ZooKeeper) sized for a laptop.

## Push vs Pull Ingestion

- External sources are **pull** (polling APIs) — we don't control them.
- Internal telemetry is **push** (producers → Kafka).
- Bridge producers convert pull → push for streaming consumers.

## Real vs Simulated Telemetry

- **Chosen: simulated (primary) + real where free.** Real public telemetry is sparse, unlabelled, rate-limited. Synthetic data gives volume + labelled anomalies; real APIs (FIRMS/POWER/SWPC/CelesTrak) provide authenticity.

## Airflow vs Alternatives (Dagster/Prefect/cron)

- **Chosen: Airflow.** Already in the Phase 7 stack, mature scheduling/retries, large connector ecosystem.
- Trade-off: heavier than cron/Prefect; run as single-process standalone LocalExecutor to fit memory.

## Schema Registry: Confluent vs In-code

- **Chosen: lightweight in-code specs.** Avoids running a registry service on a 16 GB laptop; sufficient for MVP validation.

## Cross References

- [16-adr.md](16-adr.md) · [architecture/13-trade-offs.md](../../architecture/13-trade-offs.md)
