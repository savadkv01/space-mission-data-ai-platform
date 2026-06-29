# 17 - Architecture Decision Records

> **Phase 6 - Data Modeling** · Document 17 of 18

## ADR-01: Medallion Architecture
Status: Accepted. Bronze/Silver/Gold gives clear quality gates, replayability, and reuse. Alt: single layer — rejected (no traceability).

## ADR-02: Star Schema for Gold
Status: Accepted. Fast joins on DuckDB, interview-standard. Alt: Data Vault — rejected, over-engineered for one team/laptop.

## ADR-03: Time-Series Modeling
Status: Accepted. Telemetry/orbit need partitioned tiered aggregates for anomaly ML. Alt: store raw only — rejected, slow.

## ADR-04: Feature Store
Status: Accepted. Point-in-time correctness, reuse, no leakage. Alt: inline compute — rejected, duplication.

## ADR-05: Vector Database
Status: Accepted. RAG over mission knowledge + telemetry semantics. Alt: keyword search — rejected, weak grounding.

## ADR-06: Iceberg Format
Status: Accepted. Schema evolution + time-travel + compaction. Alt: plain Parquet — rejected, no ACID/versioning.
