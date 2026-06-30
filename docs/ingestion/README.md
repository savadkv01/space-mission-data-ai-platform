# Phase 8 — Data Ingestion (Design Docs)

Engineering design for the ingestion layer. Implementation lives in [`ingestion/`](../../ingestion/).

| # | Document |
| --- | --- |
| 01 | [Overview](01-overview.md) |
| 02 | [Streaming Design (Kafka)](02-streaming-design.md) |
| 03 | [Batch Design (Airflow)](03-batch-design.md) |
| 04 | [API Ingestion](04-api-ingestion.md) |
| 05 | [File Ingestion](05-file-ingestion.md) |
| 06 | [Simulation](06-simulation.md) |
| 07 | [Landing Zone](07-landing-zone.md) |
| 08 | [Schema Strategy](08-schema-strategy.md) |
| 09 | [Data Quality](09-data-quality.md) |
| 10 | [Error Handling](10-error-handling.md) |
| 11 | [Observability](11-observability.md) |
| 12 | [Latency](12-latency.md) |
| 13 | [Scalability](13-scalability.md) |
| 14 | [Security](14-security.md) |
| 15 | [Trade-offs](15-trade-offs.md) |
| 16 | [ADRs](16-adr.md) |
| 17 | [Glossary](17-glossary.md) |

## Related

- Code: [ingestion/](../../ingestion/) · run guide: [ingestion/README.md](../../ingestion/README.md)
- Source verification: [tools/datasource-preflight/](../../tools/datasource-preflight/)
- Data architecture: [architecture/06-data-architecture.md](../../architecture/06-data-architecture.md)
- Bronze model: [docs/data-modeling/02-bronze-layer.md](../data-modeling/02-bronze-layer.md)
