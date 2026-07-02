-- Certified dataset: wildfire_daily  (Superset virtual dataset)
-- Owner: EO Operations Lead  |  Layer: serving  |  Grain: 1 row / AOI / day
-- Source of truth: serving.serving_wildfire_daily (dbt data product, UC-15).
-- BI NEVER re-derives severity or corroboration — they are pre-computed in the
-- serving product so BI and API always agree (semantic-layer contract).
--
-- Superset database connection: `serving_duckdb`
--   duckdb:////opt/serving/serving.duckdb  (read-only, httpfs + parquet loaded)
--
-- Refresh: warmed by the Airflow `serving_refresh` DAG; cache TTL 1h.
select
    aoi_key,
    aoi_name,
    cast(date_key as date)          as event_date,
    detections,
    mean_frp,
    max_frp,
    area_km2,
    severity,                       -- extreme | high | moderate | low | unknown
    ems_corroborated                -- boolean: EMS ground-truth match
from serving.serving_wildfire_daily
