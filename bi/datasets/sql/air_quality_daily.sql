-- Certified dataset: air_quality_daily  (Superset virtual dataset)  [CLIMATE-EXT 12b]
-- Owner: Air-Quality Lead  |  Layer: serving  |  Grain: 1 row / AOI / day
-- Source of truth: serving.serving_air_quality_daily (Phase 11b data product).
-- Pre-denormalized (dim_aoi already joined upstream) so BI has zero runtime joins.
-- AQI bands are pre-computed upstream (US-EPA scheme); BI displays, never derives.
--
-- Superset database connection: `serving_duckdb`
-- Refresh: rebuilt by the `serving_refresh` DAG; cache TTL 1h.
select
    aoi_key,
    aoi_name,
    cast(date_key as date)          as event_date,
    pm25_mean,
    pm25_max,
    pm10_mean,
    pm10_max,
    no2_column_mean,
    so2_column_mean,
    co_column_mean,
    o3_column_mean,
    station_count,
    aqi_pm25,
    aqi_pm10,
    aqi_band,
    exceedance_flag,
    area_km2
from serving.serving_air_quality_daily
