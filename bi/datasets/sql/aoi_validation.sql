-- Certified dataset: aoi_validation  (Superset virtual dataset)
-- Owner: EO Operations Lead  |  Layer: serving  |  Grain: 1 row / AOI
-- Source of truth: serving.serving_aoi_validation (dbt data product, UC-27).
-- Copernicus-EMS ground-truth corroboration — the platform's trust signal.
--
-- Superset database connection: `serving_duckdb`
select
    aoi_key,
    event_type,                     -- fire | flood
    cast(event_date as date)        as event_date,
    area_km2,
    evidence_days,
    corroborated,
    trust                           -- corroborated | unconfirmed
from serving.serving_aoi_validation
