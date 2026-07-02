-- Certified dataset: platform_daily  (Superset virtual dataset)  [EXECUTIVE]
-- Owner: Platform Lead  |  Layer: serving_agg  |  Grain: 1 row / day
-- Source of truth: serving_agg.mv_kpi_platform_daily (pre-computed rollup).
-- The executive dashboard reads this ONE small table instead of scanning every
-- wide product — the caching / latency SLA depends on it (materialized tier).
--
-- Superset database connection: `serving_duckdb`
-- Refresh: rebuilt by the `serving_refresh` DAG; cache TTL 15min.
select
    cast(date_key as date)          as kpi_date,
    fire_detections,
    peak_frp,
    fire_aois,
    flood_aoi_days,
    flood_aois,
    vessel_days,
    suspicious_vessels
from serving_agg.mv_kpi_platform_daily
