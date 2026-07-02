-- Certified dataset: flood_daily  (Superset virtual dataset)
-- Owner: EO Operations Lead  |  Layer: serving  |  Grain: 1 row / AOI / day
-- Source of truth: serving.serving_flood_daily (dbt data product, UC-16).
-- flood_flag is computed in the serving product (NDWI threshold), never in BI.
--
-- Superset database connection: `serving_duckdb`
-- Refresh: warmed by the Airflow `serving_refresh` DAG; cache TTL 1h.
select
    aoi_key,
    aoi_name,
    cast(date_key as date)          as event_date,
    ndwi_mean,
    ndwi_max,
    valid_pixel_fraction,
    flood_flag,                     -- boolean: AOI-day classified as flooded
    area_km2,
    ems_corroborated
from serving.serving_flood_daily
