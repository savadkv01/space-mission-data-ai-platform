# 16 - Architecture Decision Records (Ingestion)

> **Phase 8 - Data Ingestion** · Document 16 of 17

Format: Context · Decision · Consequences. Status: Accepted unless noted.

## ADR-08-01: Kafka for Streaming Ingestion

- **Context:** Need replayable, partitioned, low-latency intake for telemetry/events.
- **Decision:** Use Apache Kafka (single-broker KRaft) as the streaming backbone.
- **Consequences:** + replay, parallelism, DLQ, ecosystem; − heavier than a simple queue (mitigated by single-node sizing).

## ADR-08-02: Airflow for Batch Ingestion

- **Context:** Scheduled, retryable pulls from external APIs/files.
- **Decision:** Use Airflow (standalone LocalExecutor) with thin DAGs calling a shared ingest task.
- **Consequences:** + mature scheduling/retries, reuse Phase 7 infra; − memory footprint (mitigated by standalone mode).

## ADR-08-03: Synthetic Telemetry Is Required

- **Context:** Real public telemetry is sparse, unlabelled, rate-limited.
- **Decision:** Build seeded generators (telemetry/orbit/weather) with injectable, labelled anomalies.
- **Consequences:** + volume, reproducibility, ML labels, offline demos; − synthetic ≠ real distribution (documented; real feeds supplement).

## ADR-08-04: MinIO as the Landing Zone

- **Context:** Need S3-compatible, local, open object storage for Bronze.
- **Decision:** Land Bronze as NDJSON under `s3://bronze/<source>/ingest_date=.../`.
- **Consequences:** + S3 API parity, cheap, Hive-style partitions; − object store (not a DB) — querying needs Spark/DuckDB downstream.

## ADR-08-05: Hybrid (Streaming + Batch) Ingestion Model

- **Context:** Sources differ in cadence and volume.
- **Decision:** Route each source to streaming or batch; both converge on Bronze.
- **Consequences:** + right tool per source, single source of truth; − two code paths to maintain.

## ADR-08-06: At-Least-Once + Checksum Dedup

- **Context:** Must not lose data; must avoid duplicates.
- **Decision:** Manual offset commit after durable write; idempotent producers; `_checksum` dedup.
- **Consequences:** + no loss, effectively-once at Bronze; − possible transient duplicates before dedup.

## ADR-08-07: Lightweight In-code Schema Registry

- **Context:** Avoid running a registry service on a laptop.
- **Decision:** Declarative `Schema`/`FieldSpec` in code; schema-on-read at Bronze.
- **Consequences:** + simple, testable; − less central governance than a managed registry (acceptable for MVP).

## Cross References

- [15-trade-offs.md](15-trade-offs.md) · [architecture/14-adr.md](../../architecture/14-adr.md)
