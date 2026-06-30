# Transformation Layer Documentation (Phase 9)

> **Phase 9 - Data Transformation (Lakehouse Processing Layer)**

This folder is the enterprise design specification for the transformation layer. It is realised by the code under [`transformation/`](../../transformation/).

## Document Index

| # | Document | Task |
| --- | --- | --- |
| 01 | [Overview](01-overview.md) | 1 |
| 02 | [Processing Engines](02-processing-engines.md) | 2 |
| 03 | [Bronze → Silver](03-bronze-silver.md) | 3 |
| 04 | [Silver → Gold](04-silver-gold.md) | 4 |
| 05 | [Streaming Processing](05-streaming-processing.md) | 5 |
| 06 | [Batch Processing](06-batch-processing.md) | 6 |
| 07 | [Cleaning Framework](07-cleaning-framework.md) | 7 |
| 08 | [Feature Engineering](08-feature-engineering.md) | 8 |
| 09 | [Aggregation](09-aggregation.md) | 9 |
| 10 | [Geospatial](10-geospatial.md) | 10 |
| 11 | [Time Series](11-time-series.md) | 11 |
| 12 | [Data Quality](12-data-quality.md) | 12 |
| 13 | [Lineage](13-lineage.md) | 13 |
| 14 | [Performance](14-performance.md) | 14 |
| 15 | [Error Handling](15-error-handling.md) | 15 |
| 16 | [Observability](16-observability.md) | 16 |
| 17 | [Trade-offs](17-trade-offs.md) | 17 |
| 18 | [ADRs](18-adr.md) | 18 |
| 19 | [Glossary](19-glossary.md) | — |

## Status

Design + reference implementation complete. Infrastructure (Spark, Kafka, MinIO, Airflow) is **not yet provisioned** — the pure-Python transformation rules and the offline demo run today; Spark/dbt/Airflow entrypoints activate when infra lands.
