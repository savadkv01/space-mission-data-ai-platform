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
SELECT aoi_key, aoi_name, event_type, region, area_km2, geo_key
FROM read_parquet('s3://gold/ref_aoi/*.parquet');

-- --- Data products (materialized serving tables) ------------------------------
CREATE SCHEMA IF NOT EXISTS serving;

-- Wildfire observation freshness (UC-15 publication gate; one row per region)
CREATE OR REPLACE TABLE serving.serving_wildfire_freshness AS
WITH regions AS (
    SELECT DISTINCT region FROM semantic.dim_aoi WHERE region IS NOT NULL
),
obs AS (
    SELECT region,
           MAX(TRY_CAST(event_ts AS TIMESTAMPTZ)) AS latest_observation_ts,
           COUNT(*)                               AS detections_total
    FROM read_parquet('s3://gold/fire_aoi_attribution/*.parquet')
    WHERE region IS NOT NULL
    GROUP BY region
),
evaluated AS (
    SELECT
        r.region,
        o.latest_observation_ts,
        COALESCE(o.detections_total, 0)        AS detections_total,
        NOW()                                  AS freshness_evaluated_at,
        6                                      AS max_observation_age_hours
    FROM regions r
    LEFT JOIN obs o ON o.region = r.region
)
SELECT
    region,
    latest_observation_ts,
    freshness_evaluated_at,
    ROUND(DATE_DIFF('second', latest_observation_ts, freshness_evaluated_at) / 3600.0, 3) AS observation_age_hours,
    max_observation_age_hours,
    detections_total,
    CASE
        WHEN latest_observation_ts IS NULL THEN 'no_observations'
        WHEN DATE_DIFF('second', latest_observation_ts, freshness_evaluated_at) / 3600.0
             BETWEEN 0 AND max_observation_age_hours THEN 'current'
        ELSE 'stale'
    END AS freshness_status,
    CASE
        WHEN DATE_DIFF('second', latest_observation_ts, freshness_evaluated_at) / 3600.0
             BETWEEN 0 AND max_observation_age_hours THEN 'exploratory'
        ELSE 'blocked'
    END AS publication_status
FROM evaluated;

-- Wildfire Activity (UC-15)
CREATE OR REPLACE TABLE serving.serving_wildfire_daily AS
SELECT
    f.aoi_key,
    a.aoi_name,
    a.region,
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
    (c.aoi_key IS NOT NULL) AS ems_corroborated,
    s.latest_observation_ts,
    s.observation_age_hours,
    COALESCE(s.freshness_status, 'no_observations') AS freshness_status,
    COALESCE(s.publication_status, 'blocked')       AS publication_status
FROM read_parquet('s3://gold/kpi_wildfire_aoi_daily/*.parquet') f
LEFT JOIN semantic.dim_aoi a ON f.aoi_key = a.aoi_key
LEFT JOIN serving.serving_wildfire_freshness s ON s.region = a.region
LEFT JOIN (
    SELECT DISTINCT aoi_key FROM read_parquet('s3://gold/kpi_aoi_validation/*.parquet')
    WHERE event_type = 'fire' AND corroborated
) c ON f.aoi_key = c.aoi_key;

-- Flood Extent (UC-16)
CREATE OR REPLACE TABLE serving.serving_flood_daily AS
SELECT
    f.aoi_key, a.aoi_name, a.region, f.date_key,
    f.ndwi_mean, f.ndwi_max, f.valid_pixel_fraction, f.flood_flag,
    a.area_km2,
    (c.aoi_key IS NOT NULL) AS ems_corroborated
FROM read_parquet('s3://gold/kpi_flood_aoi_daily/*.parquet') f
LEFT JOIN semantic.dim_aoi a ON f.aoi_key = a.aoi_key
LEFT JOIN (
    SELECT DISTINCT aoi_key FROM read_parquet('s3://gold/kpi_aoi_validation/*.parquet')
    WHERE event_type = 'flood' AND corroborated
) c ON f.aoi_key = c.aoi_key;

-- Maritime Activity (UC-18, area-based GFW 4Wings; 1 row / maritime AOI / day)
CREATE OR REPLACE TABLE serving.serving_maritime_activity_daily AS
SELECT
    m.aoi_key, a.aoi_name, a.region, m.date_key,
    m.fishing_hours, m.fishing_vessels, m.fishing_status,
    m.presence_hours, m.presence_vessels, m.presence_status,
    m.sar_detections, m.sar_unmatched_detections, m.sar_dark_fraction, m.sar_status
FROM read_parquet('s3://gold/fact_maritime_activity_daily/*.parquet') m
LEFT JOIN semantic.dim_aoi a ON m.aoi_key = a.aoi_key;

-- Maritime Vessel Activity (UC-18) - DEMONSTRATOR (identity-search sample)
CREATE OR REPLACE TABLE serving.serving_vessel_activity AS
SELECT
    vessel_key, date_key, transmissions, flag, vessel_type, active_span_days,
    suspicious_flag,
    CASE WHEN suspicious_flag THEN 'high' ELSE 'normal' END AS review_priority,
    'identity_completeness_heuristic' AS signal_basis,
    'pending' AS domain_review_status
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
