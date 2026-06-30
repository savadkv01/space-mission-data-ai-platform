# 09 - Data Aggregation Strategy

> **Phase 9 - Data Transformation** · Document 09 of 19

## Aggregation Dimensions

| Dimension | Grain(s) | Example |
| --- | --- | --- |
| Time | minute (60s), hour (3600s), day (86400s) | per-minute anomaly count |
| Satellite | per `satellite_id` | daily health score |
| Mission | per `mission_key` (roll-up of satellites) | mission uptime |
| Geospatial | 0.25° grid cell (`geo_key`) | fires per cell per day |

Code: [transformation/batch/aggregation_jobs.py](../../transformation/batch/aggregation_jobs.py) (`aggregate_time` supports time + entity grains; reducers: mean/sum/min/max/count).

## Time-based Aggregation

Timestamps are floored to fixed windows (`window_key`) and reduced per `(entity, window_start)`. Minute/hour rollups feed live dashboards; daily rollups feed Gold KPI tables.

## Satellite / Mission Aggregation

Satellite-level metrics aggregate to mission-level via the `dim_satellite → dim_mission` relationship (Phase 6). Mission rollups are computed in dbt from satellite Gold tables.

## Geospatial Aggregation

Observations are snapped to a 0.25° grid (`geo_key`) and counted/averaged per cell — compact and join-friendly for the EO marts (see [10-geospatial.md](10-geospatial.md)).

## Raw vs Aggregated Storage — Trade-off

| | Raw (Silver) | Pre-aggregated (Gold) |
| --- | --- | --- |
| Query speed | slow (scan + group) | fast (pre-computed) |
| Flexibility | any question | fixed grains |
| Storage | large | small |
| Freshness | live | batch-refreshed |

**Decision:** keep raw in Silver for flexibility + reprocessing; pre-aggregate the **known dashboard grains** into Gold to avoid runtime joins. On-demand questions outside those grains run against Silver via DuckDB/Spark-SQL. See [17-trade-offs.md](17-trade-offs.md).

## Cross References

- [04-silver-gold.md](04-silver-gold.md) · [14-performance.md](14-performance.md) · [data-modeling/11-granularity.md](../data-modeling/11-granularity.md)
