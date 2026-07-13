-- Certified dataset: vegetation_health_daily  (Superset virtual dataset)  [CLIMATE-EXT 12b]
-- Owner: Climate Analytics Lead  |  Layer: serving  |  Grain: 1 row / AOI / day
-- Source of truth: serving.serving_vegetation_health_daily (Phase 11b data product).
-- NDVI/EVI greenness, 30-day NDVI trend + direction, valid-pixel coverage, the
-- pre-computed vegetation-health band, and the crop-stress proxy flag.
--
-- Superset database connection: `serving_duckdb`
-- Refresh: rebuilt by the `serving_refresh` DAG; cache TTL 1h.
select
    aoi_key,
    aoi_name,
    cast(date_key as date)          as event_date,
    ndvi_mean,
    ndvi_max,
    evi_mean,
    ndvi_trend_30d,
    ndvi_trend_dir,
    valid_pixel_fraction,
    ndvi_health_band,
    ndvi_health_label,
    crop_stress_flag,
    area_km2
from serving.serving_vegetation_health_daily
