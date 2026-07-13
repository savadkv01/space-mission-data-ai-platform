-- Certified dataset: climate_daily  (Superset virtual dataset)  [CLIMATE-EXT 12b · EXECUTIVE]
-- Owner: Platform Lead  |  Layer: serving_agg  |  Grain: 1 row / day
-- Source of truth: serving_agg.mv_kpi_climate_daily (Phase 11b pre-computed rollup).
-- Mirrors platform_daily: the executive and weather dashboards read this ONE small
-- table instead of scanning the four wide climate products — the caching / latency
-- SLA depends on it (materialized tier).
--
-- Superset database connection: `serving_duckdb`
-- Refresh: rebuilt by the `serving_refresh` DAG; cache TTL 15min.
select
    cast(date_key as date)          as kpi_date,
    mean_aqi_pm25,
    aqi_exceedance_days,
    air_quality_aois,
    dust_event_days,
    peak_aod,
    dust_aois,
    mean_lst_anomaly,
    warming_days,
    desertification_days,
    mean_ndvi,
    crop_stress_days
from serving_agg.mv_kpi_climate_daily
