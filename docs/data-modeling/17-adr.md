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
Status: Accepted for the scale tier; **superseded for the MVP by ADR-10**. Iceberg gives schema evolution + time-travel + compaction once infrastructure is provisioned. Alt: plain Parquet — chosen for the MVP tier (see ADR-10).

## ADR-07: AOI Point-in-Polygon Join (dual path)
Status: Accepted. Cluster uses Spark + Sedona/H3; the offline path and tests use a dependency-free ray-casting point-in-polygon with a bbox pre-filter so behaviour is identical on a 16 GB laptop. Alt: require Sedona everywhere — rejected, too heavy for local/tests.

## ADR-08: Copernicus EMS as Reference Layer
Status: Accepted. EMS has no clean public JSON API, so activation footprints are downloaded from the portal and landed via the file connector as a manually refreshed `ref_aoi` reference/ground-truth layer — not an automated API connector. Enables cross-source validation (`kpi_aoi_validation`). Alt: scrape the portal — rejected, fragile and out of pattern.

## ADR-09: Spacecraft Track Excluded from MVP, Retained as Simulation
Status: Accepted. Telemetry/orbit/space-weather use cases (UC-01/02/03) ranked 25–27 of 30 with Data Availability 1/5; their pipelines run on synthetic generators, so anchoring MVP flagship use cases on fabricated data would break the platform's open-data credibility and force circular KPI validation. Decision: keep the built pipelines as a labelled post-MVP **Simulation Track** (streaming + anomaly-ML demonstrator), tagged `Sim` in the Silver entity inventory. Alt A: promote to MVP — rejected (scope creep, weak realism). Alt B: delete — rejected (discards working streaming/time-series assets).

## ADR-10: Parquet for the MVP Tier, Iceberg Deferred to Scale Tier
Status: Accepted (refines ADR-06 / architecture ADR-002). Context: the ADRs marked Iceberg unconditionally "Accepted", but the actual Spark code writes plain Parquet everywhere (`bronze_to_silver.run_spark` → `.write.parquet`, `spark_streaming` → `writeStream.format("parquet")`, DuckDB `read_parquet`), and the MVP does full-overwrite Silver writes with a single writer — none of Iceberg's ACID / time-travel / row-level-delete features are exercised. Running the extra `iceberg-rest` JVM catalog service also competes for scarce RAM on the 16 GB target. Decision: two tiers — **(1) MVP / local tier:** Parquet on MinIO + DuckDB (matches the code, zero extra services); **(2) scale tier:** promote to Iceberg when a concrete trigger fires. Triggers: concurrent multi-writer jobs, row-level upserts/deletes (e.g. GDPR erasure), time-travel/audit requirement, tables large enough to need managed compaction, or multiple engines writing the same tables. Alt A: commit to Iceberg now — rejected (unused features, extra service, contradicts code on a 16 GB laptop). Alt B: delete Iceberg from the vision — rejected (loses the lakehouse endgame + interview narrative). Alt C: Delta Lake — rejected per 13-trade-offs (engine neutrality preferred for the eventual scale tier).
