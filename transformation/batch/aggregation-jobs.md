# Design — Aggregation Jobs

> Code: [aggregation_jobs.py](aggregation_jobs.py) · Spec: [docs/transformation/09-aggregation.md](../../docs/transformation/09-aggregation.md)

## `aggregate_time`

Generic time-window aggregation over a value field, optionally per entity.

| Param | Meaning |
| --- | --- |
| `grain` | `minute` (60s), `hour` (3600s), `day` (86400s) |
| `key_fields` | entity grouping (e.g. `["satellite_id"]`) |
| `agg` | `mean` / `sum` / `min` / `max` / `count` |

Output: one row per `(entity…, window_start)` with `<value>_<agg>` and `count`.

## Granularity catalogue

| Dimension | Grains |
| --- | --- |
| Time | minute, hour, day |
| Entity | satellite, mission |
| Geo | 0.25° grid cell (`geo_key`) |

## Raw vs aggregated

Raw kept in Silver (flexibility, reprocessing); known dashboard grains pre-aggregated into Gold (speed, no runtime joins). Exploratory questions run on Silver via DuckDB/Spark-SQL.
