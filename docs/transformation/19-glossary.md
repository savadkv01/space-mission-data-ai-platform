# 19 - Glossary

> **Phase 9 - Data Transformation** · Document 19 of 19

| Term | Definition |
| --- | --- |
| **Medallion architecture** | Bronze (raw) → Silver (clean) → Gold (curated) layering pattern. |
| **Bronze** | Raw, immutable, replayable landing layer (Phase 8). |
| **Silver** | Cleaned, typed, deduplicated, conformed single source of truth. |
| **Gold** | Curated business-ready aggregates/KPIs; dashboard-shaped. |
| **Conformance** | Standardizing units, names, types, and timestamps to a canonical schema. |
| **Deduplication** | Keeping one row per natural key (latest by event time). |
| **Quarantine** | Dataset of rejected records with machine-readable reasons. |
| **Watermark** | Event-time bound past which late events are dropped from streaming state. |
| **Micro-batch** | Small batch processed on each streaming trigger. |
| **Window (tumbling/sliding)** | Fixed time interval over which events are aggregated. |
| **Checkpoint** | Persisted streaming state/offsets for exactly-once recovery. |
| **Feature** | Derived ML input keyed by `(entity_id, event_ts, namespace)`. |
| **Train/serve skew** | Mismatch between training and serving feature computation. |
| **geo_key** | Grid-cell spatial key (`grid_lat:grid_lon`) for geospatial joins/aggregation. |
| **Lineage** | Record of inputs→outputs, counts, code version per run. |
| **Code fingerprint** | Hash of rule identifiers used to version transformation logic. |
| **dbt** | SQL transformation/test/lineage framework for the Gold layer. |
| **DuckDB** | In-process SQL engine used as a laptop-friendly warehouse. |
| **Iceberg / Delta** | Open table formats adding ACID, schema evolution, time-travel. |
| **Parquet** | Columnar file format used across Silver/Gold. |
| **Kp index** | Geomagnetic activity scale (0–9); ≥5 indicates a storm. |
| **FRP** | Fire Radiative Power — fire intensity in EO data. |
| **AQE** | Spark Adaptive Query Execution. |
| **Idempotent** | Re-running produces the same result (partition overwrite + dedup). |

## Cross References

- [docs/data-modeling/18-glossary.md](../data-modeling/18-glossary.md) · [docs/ingestion/17-glossary.md](../ingestion/17-glossary.md)
