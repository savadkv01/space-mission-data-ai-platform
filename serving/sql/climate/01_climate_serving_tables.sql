-- =============================================================================
-- Serving Layer — Climate / Dust / Air-Quality DDL (Phase 11b, Task 4)
-- =============================================================================
-- Engine-agnostic reference for the climate serving tables + dimensions that the
-- dbt models under ../../dbt/models/climate build. Use this when standing up the
-- serving warehouse directly (no dbt), or as documentation of the physical
-- serving contract. Gold Parquet is read from MinIO via the httpfs extension.
--
-- Mirrors sql/01_serving_tables.sql for the MVP products.
-- =============================================================================

INSTALL httpfs; LOAD httpfs;

CREATE SCHEMA IF NOT EXISTS semantic;
CREATE SCHEMA IF NOT EXISTS serving;

-- --- Semantic reference dimensions (static) ----------------------------------
CREATE OR REPLACE VIEW semantic.dim_pollutant AS
SELECT * FROM (VALUES
    ('PM25', 'Fine Particulate Matter', 'surface_concentration', 'µg/m³', 'US_EPA', 15.0, 15.0,
     CAST('[{"aqi_low":0,"aqi_high":50,"value_low":0.0,"value_high":12.0,"label":"Good"},{"aqi_low":51,"aqi_high":100,"value_low":12.1,"value_high":35.4,"label":"Moderate"},{"aqi_low":101,"aqi_high":150,"value_low":35.5,"value_high":55.4,"label":"Unhealthy (sensitive)"},{"aqi_low":151,"aqi_high":200,"value_low":55.5,"value_high":150.4,"label":"Unhealthy"},{"aqi_low":201,"aqi_high":300,"value_low":150.5,"value_high":250.4,"label":"Very Unhealthy"},{"aqi_low":301,"aqi_high":500,"value_low":250.5,"value_high":500.4,"label":"Hazardous"}]' AS JSON),
     CAST('[]' AS JSON)),
    ('PM10', 'Coarse Particulate Matter', 'surface_concentration', 'µg/m³', 'US_EPA', 45.0, 45.0,
     CAST('[{"aqi_low":0,"aqi_high":50,"value_low":0.0,"value_high":54.0,"label":"Good"},{"aqi_low":51,"aqi_high":100,"value_low":55.0,"value_high":154.0,"label":"Moderate"},{"aqi_low":101,"aqi_high":150,"value_low":155.0,"value_high":254.0,"label":"Unhealthy (sensitive)"},{"aqi_low":151,"aqi_high":200,"value_low":255.0,"value_high":354.0,"label":"Unhealthy"},{"aqi_low":201,"aqi_high":300,"value_low":355.0,"value_high":424.0,"label":"Very Unhealthy"},{"aqi_low":301,"aqi_high":500,"value_low":425.0,"value_high":604.0,"label":"Hazardous"}]' AS JSON),
     CAST('[]' AS JSON)),
    ('NO2', 'Nitrogen Dioxide', 'column_density', 'mol/m²', 'n/a', CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST('[]' AS JSON), CAST('[]' AS JSON)),
    ('SO2', 'Sulphur Dioxide', 'column_density', 'mol/m²', 'n/a', CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST('[]' AS JSON), CAST('[]' AS JSON)),
    ('CO', 'Carbon Monoxide', 'column_density', 'mol/m²', 'n/a', CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST('[]' AS JSON), CAST('[]' AS JSON)),
    ('O3', 'Ozone', 'column_density', 'mol/m²', 'n/a', CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST('[]' AS JSON), CAST('[]' AS JSON)),
    ('CH4', 'Methane', 'column_density', 'ppb', 'n/a', CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST('[]' AS JSON), CAST('[]' AS JSON)),
    ('AOD', 'Aerosol Optical Depth', 'optical', 'unitless', 'n/a', CAST(NULL AS DOUBLE), 0.5,
     CAST('[]' AS JSON),
     CAST('[{"band":0,"label":"Clear","value_low":0.0,"value_high":0.2},{"band":1,"label":"Hazy","value_low":0.2,"value_high":0.5},{"band":2,"label":"Dusty","value_low":0.5,"value_high":1.0},{"band":3,"label":"Heavy dust","value_low":1.0,"value_high":2.0},{"band":4,"label":"Severe","value_low":2.0,"value_high":5.0}]' AS JSON))
) AS t(pollutant_code, pollutant_name, measure_type, canonical_unit, aqi_scheme, who_guideline, exceedance_threshold, aqi_breakpoints, severity_bands);

CREATE OR REPLACE VIEW semantic.dim_climate_indicator AS
SELECT * FROM (VALUES
    ('LST', 'Land Surface Temperature', '°C', 'MODIS/Landsat', 'daily', CAST(NULL AS JSON), CAST('[]' AS JSON), false),
    ('LST_ANOM', 'LST Anomaly (same-DOY)', '°C', 'derived', 'daily', CAST(NULL AS JSON),
     CAST('[{"band":-1,"label":"Cooler","value_low":null,"value_high":-1.0},{"band":0,"label":"Normal","value_low":-1.0,"value_high":1.0},{"band":1,"label":"Warm","value_low":1.0,"value_high":3.0},{"band":2,"label":"Hot","value_low":3.0,"value_high":5.0},{"band":3,"label":"Extreme","value_low":5.0,"value_high":null}]' AS JSON), false),
    ('SST', 'Sea Surface Temperature', '°C', 'OISST', 'daily', CAST(NULL AS JSON), CAST('[]' AS JSON), false),
    ('SST_ANOM', 'SST Anomaly (same-DOY)', '°C', 'derived', 'daily', CAST(NULL AS JSON), CAST('[]' AS JSON), false),
    ('NDVI', 'Vegetation Index (NDVI)', 'index', 'Sentinel-2', '16-day', CAST('[-1.0,1.0]' AS JSON),
     CAST('[{"band":0,"label":"Bare / water","value_low":-1.0,"value_high":0.1},{"band":1,"label":"Sparse","value_low":0.1,"value_high":0.3},{"band":2,"label":"Moderate","value_low":0.3,"value_high":0.5},{"band":3,"label":"Healthy","value_low":0.5,"value_high":0.7},{"band":4,"label":"Dense","value_low":0.7,"value_high":1.0}]' AS JSON), false),
    ('EVI', 'Enhanced Vegetation Index', 'index', 'Sentinel-2', '16-day', CAST('[-1.0,1.0]' AS JSON), CAST('[]' AS JSON), false),
    ('NDWI', 'Water Index (NDWI)', 'index', 'Sentinel-2', '16-day', CAST('[-1.0,1.0]' AS JSON), CAST('[]' AS JSON), false),
    ('TREE_LOSS', 'Tree-Cover Loss', 'ha', 'GFW', 'annual', CAST(NULL AS JSON), CAST('[]' AS JSON), false),
    ('DESERT_PROXY', 'Desertification Proxy', 'index', 'derived', 'daily', CAST('[0.0,1.0]' AS JSON), CAST('[]' AS JSON), false)
) AS t(indicator_code, indicator_name, unit, source_family, native_cadence, normal_range, anomaly_bands, requires_new_ingest);

-- --- Data products (materialized serving tables) ------------------------------

-- Air Quality (exceedance_flag null unless PM evidence decides it)
CREATE OR REPLACE TABLE serving.serving_air_quality_daily AS
WITH aq AS (
    SELECT *,
        CASE
            WHEN COALESCE(exceedance_flag, false) THEN 'positive'
            WHEN pm25_mean IS NOT NULL AND pm10_mean IS NOT NULL THEN 'negative'
            WHEN pm25_mean IS NOT NULL OR pm10_mean IS NOT NULL THEN 'inconclusive'
            ELSE 'not_evaluated'
        END AS exceedance_status
    FROM read_parquet('s3://gold/fact_air_quality_daily/*.parquet')
)
SELECT
    q.aoi_key, a.aoi_name, a.region, q.date_key,
    q.pm25_mean, q.pm25_max, q.pm10_mean, q.pm10_max,
    q.no2_column_mean, q.so2_column_mean, q.co_column_mean, q.o3_column_mean,
    q.station_count, q.aqi_pm25, q.aqi_pm10, q.aqi_band, q.aqi_standard,
    CASE q.exceedance_status WHEN 'positive' THEN true WHEN 'negative' THEN false END AS exceedance_flag,
    q.exceedance_status,
    CASE
        WHEN q.pm25_mean IS NOT NULL AND q.pm10_mean IS NOT NULL THEN 'pm25_and_pm10'
        WHEN q.pm25_mean IS NOT NULL THEN 'pm25_only'
        WHEN q.pm10_mean IS NOT NULL THEN 'pm10_only'
        ELSE 'none'
    END AS pm_coverage,
    a.area_km2
FROM aq q
LEFT JOIN semantic.dim_aoi a ON q.aoi_key = a.aoi_key;

-- Dust Event (dust/transport flags null unless evidence decides them)
CREATE OR REPLACE TABLE serving.serving_dust_event_daily AS
WITH dust AS (
    SELECT *,
        CASE
            WHEN COALESCE(dust_flag, false) THEN 'positive'
            WHEN aod_mean < 0.5 OR uv_aerosol_index_mean < 1.0 THEN 'negative'
            WHEN aod_mean IS NOT NULL OR uv_aerosol_index_mean IS NOT NULL THEN 'inconclusive'
            ELSE 'not_evaluated'
        END AS dust_status,
        CASE
            WHEN COALESCE(transport_flag, false) THEN 'positive'
            WHEN corridor_aod_max < 0.5 OR wind_speed_mean <= 0 THEN 'negative'
            WHEN corridor_aod_max IS NOT NULL OR wind_speed_mean IS NOT NULL THEN 'inconclusive'
            ELSE 'not_evaluated'
        END AS transport_status
    FROM read_parquet('s3://gold/fact_dust_event_daily/*.parquet')
)
SELECT
    d.aoi_key, a.aoi_name, a.region, d.date_key,
    d.aod_mean, d.aod_max, d.uv_aerosol_index_mean,
    d.wind_speed_mean, d.wind_dir_dominant, d.corridor_aod_max, d.valid_fraction,
    d.dust_severity_band,
    CASE d.dust_severity_band
        WHEN 0 THEN 'Clear' WHEN 1 THEN 'Hazy' WHEN 2 THEN 'Dusty'
        WHEN 3 THEN 'Heavy dust' WHEN 4 THEN 'Severe' ELSE 'unknown'
    END AS dust_severity_label,
    CASE d.dust_status WHEN 'positive' THEN true WHEN 'negative' THEN false END AS dust_flag,
    d.dust_status,
    CASE d.transport_status WHEN 'positive' THEN true WHEN 'negative' THEN false END AS transport_flag,
    d.transport_status,
    a.area_km2
FROM dust d
LEFT JOIN semantic.dim_aoi a ON d.aoi_key = a.aoi_key;

-- Climate Indicator (warming/desertification flags null unless evidence decides them)
CREATE OR REPLACE TABLE serving.serving_climate_indicator_daily AS
WITH clim AS (
    SELECT *,
        CASE
            WHEN COALESCE(warming_flag, false) THEN 'positive'
            WHEN lst_anomaly_c IS NOT NULL AND sst_anomaly_c IS NOT NULL THEN 'negative'
            WHEN lst_anomaly_c IS NOT NULL OR sst_anomaly_c IS NOT NULL THEN 'inconclusive'
            ELSE 'not_evaluated'
        END AS warming_status,
        CASE
            WHEN COALESCE(desertification_flag, false) THEN 'positive'
            WHEN desertification_proxy IS NOT NULL THEN 'negative'
            ELSE 'not_evaluated'
        END AS desertification_status
    FROM read_parquet('s3://gold/fact_climate_indicator_daily/*.parquet')
)
SELECT
    c.aoi_key, a.aoi_name, a.region, c.date_key,
    c.lst_c, c.lst_anomaly_c, c.sst_c, c.sst_anomaly_c,
    v.ndvi_mean, v.evi_mean, c.ndwi_mean,
    c.tree_cover_loss_ha, c.desertification_proxy, c.lst_anomaly_band,
    CASE c.lst_anomaly_band
        WHEN -1 THEN 'Cooler' WHEN 0 THEN 'Normal' WHEN 1 THEN 'Warm'
        WHEN 2 THEN 'Hot' WHEN 3 THEN 'Extreme' ELSE 'unknown'
    END AS lst_anomaly_label,
    CASE c.warming_status WHEN 'positive' THEN true WHEN 'negative' THEN false END AS warming_flag,
    c.warming_status,
    CASE c.desertification_status WHEN 'positive' THEN true WHEN 'negative' THEN false END AS desertification_flag,
    c.desertification_status,
    a.area_km2
FROM clim c
LEFT JOIN read_parquet('s3://gold/fact_vegetation_health_daily/*.parquet') v
    ON c.aoi_key = v.aoi_key AND c.date_key = v.date_key
LEFT JOIN semantic.dim_aoi a ON c.aoi_key = a.aoi_key;

-- Vegetation Health (null trend = 'unknown'; crop_stress_flag null unless evidence decides it)
CREATE OR REPLACE TABLE serving.serving_vegetation_health_daily AS
WITH veg AS (
    SELECT *,
        CASE
            WHEN COALESCE(crop_stress_flag, false) THEN 'positive'
            WHEN ndvi_mean >= 0.3 OR ndvi_trend_30d >= 0 THEN 'negative'
            WHEN ndvi_mean IS NOT NULL OR ndvi_trend_30d IS NOT NULL THEN 'inconclusive'
            ELSE 'not_evaluated'
        END AS crop_stress_status
    FROM read_parquet('s3://gold/fact_vegetation_health_daily/*.parquet')
)
SELECT
    v.aoi_key, a.aoi_name, a.region, v.date_key,
    v.ndvi_mean, v.ndvi_max, v.evi_mean, v.ndvi_trend_30d,
    CASE
        WHEN v.ndvi_trend_30d IS NULL THEN 'unknown'
        WHEN v.ndvi_trend_30d > 0     THEN 'improving'
        WHEN v.ndvi_trend_30d < 0     THEN 'declining'
        ELSE 'flat'
    END AS ndvi_trend_dir,
    v.valid_pixel_fraction, v.ndvi_health_band,
    CASE v.ndvi_health_band
        WHEN 0 THEN 'Bare / water' WHEN 1 THEN 'Sparse' WHEN 2 THEN 'Moderate'
        WHEN 3 THEN 'Healthy' WHEN 4 THEN 'Dense' ELSE 'unknown'
    END AS ndvi_health_label,
    CASE v.crop_stress_status WHEN 'positive' THEN true WHEN 'negative' THEN false END AS crop_stress_flag,
    v.crop_stress_status,
    a.area_km2
FROM veg v
LEFT JOIN semantic.dim_aoi a ON v.aoi_key = a.aoi_key;
