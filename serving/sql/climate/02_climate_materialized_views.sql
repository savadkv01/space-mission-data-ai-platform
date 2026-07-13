-- =============================================================================
-- Serving Layer — Climate materialized aggregate (Phase 11b, Task 3)
-- =============================================================================
-- Small, dashboard-shaped daily climate rollup refreshed after the climate data
-- products rebuild. Mirrors sql/02_materialized_views.sql. Feeds the executive
-- and weather dashboards' air-quality / dust / climate KPIs.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS serving_agg;

CREATE OR REPLACE TABLE serving_agg.mv_kpi_climate_daily AS
WITH aq AS (
    SELECT date_key,
           AVG(aqi_pm25)                                    AS mean_aqi_pm25,
           SUM(CASE WHEN exceedance_flag THEN 1 ELSE 0 END) AS aqi_exceedance_days,
           COUNT(DISTINCT aoi_key)                          AS air_quality_aois
    FROM serving.serving_air_quality_daily GROUP BY date_key
),
dust AS (
    SELECT date_key,
           SUM(CASE WHEN dust_flag THEN 1 ELSE 0 END) AS dust_event_days,
           MAX(aod_mean)                              AS peak_aod,
           COUNT(DISTINCT aoi_key)                    AS dust_aois
    FROM serving.serving_dust_event_daily GROUP BY date_key
),
clim AS (
    SELECT date_key,
           AVG(lst_anomaly_c)                                    AS mean_lst_anomaly,
           SUM(CASE WHEN warming_flag THEN 1 ELSE 0 END)         AS warming_days,
           SUM(CASE WHEN desertification_flag THEN 1 ELSE 0 END) AS desertification_days
    FROM serving.serving_climate_indicator_daily GROUP BY date_key
),
veg AS (
    SELECT date_key,
           AVG(ndvi_mean)                                    AS mean_ndvi,
           SUM(CASE WHEN crop_stress_flag THEN 1 ELSE 0 END) AS crop_stress_days
    FROM serving.serving_vegetation_health_daily GROUP BY date_key
)
SELECT
    COALESCE(aq.date_key, dust.date_key, clim.date_key, veg.date_key) AS date_key,
    aq.mean_aqi_pm25,
    COALESCE(aq.aqi_exceedance_days, 0)    AS aqi_exceedance_days,
    COALESCE(aq.air_quality_aois, 0)       AS air_quality_aois,
    COALESCE(dust.dust_event_days, 0)      AS dust_event_days,
    dust.peak_aod,
    COALESCE(dust.dust_aois, 0)            AS dust_aois,
    clim.mean_lst_anomaly,
    COALESCE(clim.warming_days, 0)         AS warming_days,
    COALESCE(clim.desertification_days, 0) AS desertification_days,
    veg.mean_ndvi,
    COALESCE(veg.crop_stress_days, 0)      AS crop_stress_days
FROM aq
FULL OUTER JOIN dust ON aq.date_key = dust.date_key
FULL OUTER JOIN clim ON COALESCE(aq.date_key, dust.date_key) = clim.date_key
FULL OUTER JOIN veg  ON COALESCE(aq.date_key, dust.date_key, clim.date_key) = veg.date_key;
