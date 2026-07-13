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
    ('PM25', 'Fine Particulate Matter',   'surface_concentration', 'µg/m³',    'US_EPA', 15.0, 15.0),
    ('PM10', 'Coarse Particulate Matter', 'surface_concentration', 'µg/m³',    'US_EPA', 45.0, 45.0),
    ('NO2',  'Nitrogen Dioxide',          'column_density',        'mol/m²',   'n/a',    CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE)),
    ('SO2',  'Sulphur Dioxide',           'column_density',        'mol/m²',   'n/a',    CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE)),
    ('CO',   'Carbon Monoxide',           'column_density',        'mol/m²',   'n/a',    CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE)),
    ('O3',   'Ozone',                     'column_density',        'mol/m²',   'n/a',    CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE)),
    ('CH4',  'Methane',                   'column_density',        'ppb',      'n/a',    CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE)),
    ('AOD',  'Aerosol Optical Depth',     'optical',               'unitless', 'n/a',    CAST(NULL AS DOUBLE), 0.5)
) AS t(pollutant_code, pollutant_name, measure_type, canonical_unit, aqi_scheme, who_guideline, exceedance_threshold);

CREATE OR REPLACE VIEW semantic.dim_climate_indicator AS
SELECT * FROM (VALUES
    ('LST',          'Land Surface Temperature', '°C',    'MODIS/Landsat', 'daily'),
    ('LST_ANOM',     'LST Anomaly (same-DOY)',   '°C',    'derived',       'daily'),
    ('SST',          'Sea Surface Temperature',  '°C',    'OISST',         'daily'),
    ('SST_ANOM',     'SST Anomaly (same-DOY)',   '°C',    'derived',       'daily'),
    ('NDVI',         'Vegetation Index (NDVI)',  'index', 'Sentinel-2',    '16-day'),
    ('EVI',          'Enhanced Vegetation Index','index', 'Sentinel-2',    '16-day'),
    ('NDWI',         'Water Index (NDWI)',       'index', 'Sentinel-2',    '16-day'),
    ('TREE_LOSS',    'Tree-Cover Loss',          'ha',    'GFW',           'annual'),
    ('DESERT_PROXY', 'Desertification Proxy',    'index', 'derived',       'daily')
) AS t(indicator_code, indicator_name, unit, source_family, native_cadence);

-- --- Data products (materialized serving tables) ------------------------------

-- Air Quality
CREATE OR REPLACE TABLE serving.serving_air_quality_daily AS
SELECT
    q.aoi_key, a.aoi_name, q.date_key,
    q.pm25_mean, q.pm25_max, q.pm10_mean, q.pm10_max,
    q.no2_column_mean, q.so2_column_mean, q.co_column_mean, q.o3_column_mean,
    q.station_count, q.aqi_pm25, q.aqi_pm10, q.aqi_band, q.exceedance_flag,
    a.area_km2
FROM read_parquet('s3://gold/fact_air_quality_daily/*.parquet') q
LEFT JOIN semantic.dim_aoi a ON q.aoi_key = a.aoi_key;

-- Dust Event
CREATE OR REPLACE TABLE serving.serving_dust_event_daily AS
SELECT
    d.aoi_key, a.aoi_name, d.date_key,
    d.aod_mean, d.aod_max, d.uv_aerosol_index_mean,
    d.wind_speed_mean, d.wind_dir_dominant, d.corridor_aod_max, d.valid_fraction,
    d.dust_severity_band,
    CASE d.dust_severity_band
        WHEN 0 THEN 'Clear' WHEN 1 THEN 'Hazy' WHEN 2 THEN 'Dusty'
        WHEN 3 THEN 'Heavy dust' WHEN 4 THEN 'Severe' ELSE 'unknown'
    END AS dust_severity_label,
    d.dust_flag, d.transport_flag, a.area_km2
FROM read_parquet('s3://gold/fact_dust_event_daily/*.parquet') d
LEFT JOIN semantic.dim_aoi a ON d.aoi_key = a.aoi_key;

-- Climate Indicator
CREATE OR REPLACE TABLE serving.serving_climate_indicator_daily AS
SELECT
    c.aoi_key, a.aoi_name, c.date_key,
    c.lst_c, c.lst_anomaly_c, c.sst_c, c.sst_anomaly_c, c.ndwi_mean,
    c.tree_cover_loss_ha, c.desertification_proxy, c.lst_anomaly_band,
    CASE c.lst_anomaly_band
        WHEN -1 THEN 'Cooler' WHEN 0 THEN 'Normal' WHEN 1 THEN 'Warm'
        WHEN 2 THEN 'Hot' WHEN 3 THEN 'Extreme' ELSE 'unknown'
    END AS lst_anomaly_label,
    c.warming_flag, c.desertification_flag, a.area_km2
FROM read_parquet('s3://gold/fact_climate_indicator_daily/*.parquet') c
LEFT JOIN semantic.dim_aoi a ON c.aoi_key = a.aoi_key;

-- Vegetation Health
CREATE OR REPLACE TABLE serving.serving_vegetation_health_daily AS
SELECT
    v.aoi_key, a.aoi_name, v.date_key,
    v.ndvi_mean, v.ndvi_max, v.evi_mean, v.ndvi_trend_30d,
    CASE
        WHEN v.ndvi_trend_30d IS NULL THEN 'flat'
        WHEN v.ndvi_trend_30d > 0     THEN 'improving'
        WHEN v.ndvi_trend_30d < 0     THEN 'declining'
        ELSE 'flat'
    END AS ndvi_trend_dir,
    v.valid_pixel_fraction, v.ndvi_health_band,
    CASE v.ndvi_health_band
        WHEN 0 THEN 'Bare / water' WHEN 1 THEN 'Sparse' WHEN 2 THEN 'Moderate'
        WHEN 3 THEN 'Healthy' WHEN 4 THEN 'Dense' ELSE 'unknown'
    END AS ndvi_health_label,
    v.crop_stress_flag, a.area_km2
FROM read_parquet('s3://gold/fact_vegetation_health_daily/*.parquet') v
LEFT JOIN semantic.dim_aoi a ON v.aoi_key = a.aoi_key;
