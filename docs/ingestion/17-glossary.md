# 17 - Glossary (Ingestion)

> **Phase 8 - Data Ingestion** · Document 17 of 17

| Term | Definition |
| --- | --- |
| **Bronze** | Raw, immutable landing layer; source-shaped data wrapped in the provenance envelope. |
| **Bronze envelope** | Standard wrapper (`_ingest_id`, `_source`, `_checksum`, …) added to every raw record. |
| **Batch ingestion** | Scheduled pulls (Airflow) from APIs/files into Bronze. |
| **Streaming ingestion** | Event-driven intake via Kafka producers/consumers. |
| **Producer** | Component that writes messages to a Kafka topic. |
| **Consumer** | Component that reads messages from a Kafka topic. |
| **Consumer group** | Set of consumers sharing partitions of a topic for parallelism. |
| **Offset** | A consumer's position in a partition; committed after durable processing. |
| **At-least-once** | Delivery guarantee where messages may repeat but are never lost. |
| **DLQ** | Dead-letter queue — topic for records that fail processing/validation. |
| **Quarantine** | Storage area for invalid records, annotated with failure reasons for replay. |
| **Landing zone** | The Bronze/staging area in MinIO where ingested data first arrives. |
| **KRaft** | Kafka's built-in consensus mode (no ZooKeeper). |
| **TLE** | Two-Line Element set describing a satellite's orbit. |
| **SGP4** | Standard analytic propagator that turns a TLE into a position over time. |
| **GP** | General Perturbations element data (CelesTrak's structured TLE form). |
| **Kp index** | Global geomagnetic activity index (0–9). |
| **FIRMS / VIIRS** | NASA near-real-time active-fire products. |
| **Schema-on-read** | Interpret structure at read time; store payload as-is. |
| **Checksum** | SHA-256 of a payload used for integrity and duplicate detection. |
| **Batch id** | Unique id tagging all records from one ingestion run. |
| **Idempotent producer** | Producer config that prevents duplicate writes on retry. |
| **Back-pressure** | Buffering/slowing when consumers lag behind producers. |

## Cross References

- [docs/source-data-analysis/13-glossary.md](../source-data-analysis/13-glossary.md) · [architecture/15-glossary.md](../../architecture/15-glossary.md)
