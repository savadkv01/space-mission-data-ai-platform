-- =============================================================================
-- Serving Layer — DuckDB reference DDL (Task 4 / Task 10)
-- =============================================================================
-- Engine-agnostic reference for the serving tables + materialized aggregates
-- that the dbt models under ../dbt/models build. Use this when standing up the
-- serving warehouse directly (no dbt), or as documentation of the physical
-- serving contract. Gold Parquet is read from MinIO via the httpfs extension.
--
-- In production, swap read_parquet(...) for the lakehouse SQL engine tables and
-- replace `CREATE TABLE` with `CREATE MATERIALIZED VIEW` where supported (Trino).
-- =============================================================================

INSTALL httpfs; LOAD httpfs;

-- --- Semantic dimension -------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS semantic;
CREATE OR REPLACE VIEW semantic.dim_aoi AS
SELECT aoi_key, aoi_name, event_type, area_km2, geo_key
FROM read_parquet('s3://gold/ref_aoi/*.parquet');

-- --- Data products (materialized serving tables) ------------------------------
CREATE SCHEMA IF NOT EXISTS serving;

-- Wildfire Activity (UC-15)
CREATE OR REPLACE TABLE serving.serving_wildfire_daily AS
SELECT
    f.aoi_key,
    a.aoi_name,
    f.date_key,
    f.detections,
    f.mean_frp,
    f.max_frp,
    a.area_km2,
    CASE
        WHEN f.max_frp IS NULL THEN 'unknown'
        WHEN f.max_frp >= 100  THEN 'extreme'
        WHEN f.max_frp >= 30   THEN 'high'
        WHEN f.max_frp >= 10   THEN 'moderate'
        ELSE 'low'
    END AS severity,
    (c.aoi_key IS NOT NULL) AS ems_corroborated
FROM read_parquet('s3://gold/kpi_wildfire_aoi_daily/*.parquet') f
LEFT JOIN semantic.dim_aoi a ON f.aoi_key = a.aoi_key
LEFT JOIN (
    SELECT DISTINCT aoi_key FROM read_parquet('s3://gold/kpi_aoi_validation/*.parquet')
    WHERE event_type = 'fire' AND corroborated
) c ON f.aoi_key = c.aoi_key;

-- Flood Extent (UC-16)
CREATE OR REPLACE TABLE serving.serving_flood_daily AS
SELECT
    f.aoi_key, a.aoi_name, f.date_key,
    f.ndwi_mean, f.ndwi_max, f.valid_pixel_fraction, f.flood_flag,
    a.area_km2,
    (c.aoi_key IS NOT NULL) AS ems_corroborated
FROM read_parquet('s3://gold/kpi_flood_aoi_daily/*.parquet') f
LEFT JOIN semantic.dim_aoi a ON f.aoi_key = a.aoi_key
LEFT JOIN (
    SELECT DISTINCT aoi_key FROM read_parquet('s3://gold/kpi_aoi_validation/*.parquet')
    WHERE event_type = 'flood' AND corroborated
) c ON f.aoi_key = c.aoi_key;

-- Maritime Vessel Activity (UC-18)
CREATE OR REPLACE TABLE serving.serving_vessel_activity AS
SELECT
    vessel_key, date_key, transmissions, flag, vessel_type, active_span_days,
    suspicious_flag,
    CASE WHEN suspicious_flag THEN 'high' ELSE 'normal' END AS review_priority
FROM read_parquet('s3://gold/fact_vessel_activity/*.parquet');

-- Imagery Catalog (UC-25)
CREATE OR REPLACE TABLE serving.serving_scene_catalog AS
SELECT
    scene_key, date_key, collection, provider, platform, geo_key,
    cloud_cover, completeness_score, is_searchable,
    CASE
        WHEN NOT is_searchable          THEN 'unlisted'
        WHEN completeness_score IS NULL THEN 'listed'
        WHEN completeness_score >= 0.9  THEN 'gold'
        WHEN completeness_score >= 0.7  THEN 'silver'
        ELSE 'bronze'
    END AS quality_band
FROM read_parquet('s3://gold/fact_scene_catalog/*.parquet');

-- Detection Validation (UC-27)
CREATE OR REPLACE TABLE serving.serving_aoi_validation AS
SELECT
    aoi_key, event_type, event_date, area_km2, evidence_days, corroborated,
    CASE WHEN corroborated THEN 'corroborated' ELSE 'unconfirmed' END AS trust
FROM read_parquet('s3://gold/kpi_aoi_validation/*.parquet');
