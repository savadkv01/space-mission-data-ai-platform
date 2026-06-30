# 14 - Performance Optimization Strategy

> **Phase 9 - Data Transformation** · Document 14 of 19

## Partition Optimization

| Layer | Partition by | Reason |
| --- | --- | --- |
| Bronze | ingest date / source | replay + retention |
| Silver | `event_date` (+ `satellite_id` for telemetry) | partition pruning on time-range queries |
| Gold | `date_key` | dashboard date filters |

Avoid tiny files: target ~128 MB Parquet files; compact small partitions on a laptop with a periodic coalesce job.

## Caching Strategy

- Cache Silver DataFrames reused by multiple Gold marts within one Spark job (`.cache()` + `count()` to materialize).
- dbt views for thin staging (no storage); tables for Gold (read-optimized).

## Compute Optimization (Spark tuning)

| Setting | Value | Reason |
| --- | --- | --- |
| `spark.sql.shuffle.partitions` | 8 | avoid many tiny tasks on a laptop |
| Adaptive Query Execution | on | coalesce shuffle partitions automatically |
| `local[*]` single JVM | — | low overhead vs distributed |
| Kryo serializer | on | faster/compact serialization |
| broadcast joins | dims < 10 MB | avoid shuffle on dimension joins |

Code: [transformation/common/spark.py](../../transformation/common/spark.py)

## File Format Optimization

| Choice | Reason |
| --- | --- |
| **Parquet + Snappy** | columnar, splittable, good compression/CPU balance |
| Column pruning + predicate pushdown | scan less |
| **Iceberg (concept)** | table format for ACID, schema evolution, time-travel, hidden partitioning — target for prod |

## Laptop Guardrails (16 GB)

- Bounded streaming state via watermark (2 min).
- `max_active_runs=1` in Airflow.
- Small shuffle partition count; DuckDB for in-memory Gold marts.

## Cross References

- [09-aggregation.md](09-aggregation.md) · [17-trade-offs.md](17-trade-offs.md) · [data-modeling/14-performance.md](../data-modeling/14-performance.md)
