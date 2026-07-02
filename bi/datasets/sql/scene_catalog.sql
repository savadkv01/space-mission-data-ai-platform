-- Certified dataset: scene_catalog  (Superset virtual dataset)
-- Owner: Data Steward  |  Layer: serving  |  Grain: 1 row / scene
-- Source of truth: serving.serving_scene_catalog (dbt data product, UC-25).
-- quality_band is pre-computed in the serving product (completeness thresholds).
--
-- Superset database connection: `serving_duckdb`
select
    scene_key,
    cast(date_key as date)          as capture_date,
    collection,
    provider,
    platform,
    geo_key,
    cloud_cover,
    completeness_score,
    is_searchable,
    quality_band                    -- gold | silver | bronze | listed | unlisted
from serving.serving_scene_catalog
