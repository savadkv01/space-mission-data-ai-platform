# 17 - Trade-off Analysis

> **Phase 9 - Data Transformation** · Document 17 of 19

## Batch vs Streaming Transformation

| | Batch | Streaming |
| --- | --- | --- |
| Latency | minutes → daily | seconds |
| Correctness | authoritative | approximate (late data) |
| Cost/complexity | low | higher (state, checkpoints) |
| **Decision** | hybrid: streaming for live rollups, batch as the correctness backstop | |

## Spark vs dbt Responsibilities

| | Spark | dbt |
| --- | --- | --- |
| Best at | row-level cleaning, streaming, ML features | SQL aggregation, KPIs, tests |
| **Decision** | Spark owns Bronze→Silver + features; dbt owns Silver→Gold | |

Drawing the boundary at Silver keeps each engine in its strength and gives analysts SQL access to Gold.

## Pre-aggregation vs On-demand Computation

| | Pre-aggregate (Gold) | On-demand (Silver) |
| --- | --- | --- |
| Dashboard speed | fast | slow |
| Flexibility | fixed grains | any query |
| **Decision** | pre-aggregate known dashboard grains; on-demand for exploratory questions | |

## Lakehouse vs Warehouse Separation

| | Lakehouse (Silver/Gold on object store) | Separate warehouse |
| --- | --- | --- |
| Cost | low (open formats, one store) | higher (copy + license) |
| Openness | Parquet/Iceberg, many engines | proprietary |
| **Decision** | single lakehouse; DuckDB/Trino query Gold in place — no separate warehouse copy | |

## Cross References

- [02-processing-engines.md](02-processing-engines.md) · [18-adr.md](18-adr.md) · [architecture/13-trade-offs.md](../../architecture/13-trade-offs.md)
