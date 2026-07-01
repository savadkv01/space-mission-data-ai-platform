-- =============================================================================
-- Serving Layer — Materialized aggregates (Task 10: pre-computed aggregates)
-- =============================================================================
-- Small, dashboard-shaped rollups refreshed after the data products rebuild.
-- These are the query-cache / pre-aggregation tier that keeps executive and
-- operations dashboards under the Task 11 latency SLA.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS serving_agg;

-- Platform-wide daily KPI rollup (executive dashboard reads this single table).
CREATE OR REPLACE TABLE serving_agg.mv_kpi_platform_daily AS
WITH fire AS (
    SELECT date_key,
           SUM(detections)          AS fire_detections,
           MAX(max_frp)             AS peak_frp,
           COUNT(DISTINCT aoi_key)  AS fire_aois
    FROM serving.serving_wildfire_daily GROUP BY date_key
),
flood AS (
    SELECT date_key,
           SUM(CASE WHEN flood_flag THEN 1 ELSE 0 END) AS flood_aoi_days,
           COUNT(DISTINCT aoi_key)                     AS flood_aois
    FROM serving.serving_flood_daily GROUP BY date_key
),
vessel AS (
    SELECT date_key,
           COUNT(*)                                       AS vessel_days,
           SUM(CASE WHEN suspicious_flag THEN 1 ELSE 0 END) AS suspicious_vessels
    FROM serving.serving_vessel_activity GROUP BY date_key
)
SELECT
    COALESCE(fire.date_key, flood.date_key, vessel.date_key) AS date_key,
    COALESCE(fire.fire_detections, 0)      AS fire_detections,
    fire.peak_frp,
    COALESCE(fire.fire_aois, 0)            AS fire_aois,
    COALESCE(flood.flood_aoi_days, 0)      AS flood_aoi_days,
    COALESCE(flood.flood_aois, 0)          AS flood_aois,
    COALESCE(vessel.vessel_days, 0)        AS vessel_days,
    COALESCE(vessel.suspicious_vessels, 0) AS suspicious_vessels
FROM fire
FULL OUTER JOIN flood  ON fire.date_key = flood.date_key
FULL OUTER JOIN vessel ON COALESCE(fire.date_key, flood.date_key) = vessel.date_key;

-- Catalog-quality rollup (data-steward dashboard).
CREATE OR REPLACE TABLE serving_agg.mv_catalog_quality AS
SELECT
    collection,
    COUNT(*)                                                    AS scenes,
    AVG(CASE WHEN is_searchable THEN 1.0 ELSE 0.0 END)          AS searchable_rate,
    AVG(completeness_score)                                     AS mean_completeness,
    AVG(cloud_cover)                                            AS mean_cloud_cover
FROM serving.serving_scene_catalog
GROUP BY collection;
