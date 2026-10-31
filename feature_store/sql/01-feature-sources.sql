CREATE SCHEMA IF NOT EXISTS feast;

CREATE TABLE IF NOT EXISTS feast.source_satellite_health (
    sat_key TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    created_timestamp TIMESTAMPTZ NOT NULL,
    feature_date TEXT NOT NULL,
    samples BIGINT,
    anomaly_samples BIGINT,
    anomaly_density DOUBLE PRECISION,
    health_score DOUBLE PRECISION,
    battery_voltage_drift DOUBLE PRECISION,
    data_nature TEXT NOT NULL,
    readiness_status TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    PRIMARY KEY (sat_key, event_timestamp)
);

CREATE TABLE IF NOT EXISTS feast.source_mission_operations (
    mission_key TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    created_timestamp TIMESTAMPTZ NOT NULL,
    feature_date TEXT NOT NULL,
    uptime_fraction DOUBLE PRECISION,
    anomaly_count BIGINT,
    operational_state TEXT,
    data_nature TEXT NOT NULL,
    readiness_status TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    PRIMARY KEY (mission_key, event_timestamp)
);

CREATE TABLE IF NOT EXISTS feast.source_orbit_stability (
    sat_key TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    created_timestamp TIMESTAMPTZ NOT NULL,
    feature_date TEXT NOT NULL,
    altitude_drift_km DOUBLE PRECISION,
    velocity_variance_km2_s2 DOUBLE PRECISION,
    decay_rate_km_day DOUBLE PRECISION,
    data_nature TEXT NOT NULL,
    readiness_status TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    PRIMARY KEY (sat_key, event_timestamp)
);

CREATE TABLE IF NOT EXISTS feast.source_launch_performance (
    provider_key TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    created_timestamp TIMESTAMPTZ NOT NULL,
    feature_date TEXT NOT NULL,
    launches BIGINT,
    success_rate DOUBLE PRECISION,
    cadence_per_month DOUBLE PRECISION,
    mean_delay_days DOUBLE PRECISION,
    data_nature TEXT NOT NULL,
    readiness_status TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    PRIMARY KEY (provider_key, event_timestamp)
);

CREATE TABLE IF NOT EXISTS feast.source_space_weather (
    weather_scope_key TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    created_timestamp TIMESTAMPTZ NOT NULL,
    feature_date TEXT NOT NULL,
    max_kp_index DOUBLE PRECISION,
    mean_kp_index DOUBLE PRECISION,
    storm_events BIGINT,
    data_nature TEXT NOT NULL,
    readiness_status TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    PRIMARY KEY (weather_scope_key, event_timestamp)
);

CREATE TABLE IF NOT EXISTS feast.source_wildfire_aoi_daily (
    aoi_key TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    created_timestamp TIMESTAMPTZ NOT NULL,
    feature_date TEXT NOT NULL,
    detections BIGINT,
    mean_frp DOUBLE PRECISION,
    max_frp DOUBLE PRECISION,
    ems_corroborated BOOLEAN,
    area_km2 DOUBLE PRECISION,
    data_nature TEXT NOT NULL,
    readiness_status TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    PRIMARY KEY (aoi_key, event_timestamp)
);

CREATE TABLE IF NOT EXISTS feast.source_spectral_index_daily (
    aoi_key TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    created_timestamp TIMESTAMPTZ NOT NULL,
    feature_date TEXT NOT NULL,
    ndvi_mean DOUBLE PRECISION,
    ndwi_mean DOUBLE PRECISION,
    nbr_mean DOUBLE PRECISION,
    valid_pixel_fraction DOUBLE PRECISION,
    data_nature TEXT NOT NULL,
    readiness_status TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    PRIMARY KEY (aoi_key, event_timestamp)
);

CREATE TABLE IF NOT EXISTS feast.source_scene_catalog (
    scene_key TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    created_timestamp TIMESTAMPTZ NOT NULL,
    feature_date TEXT NOT NULL,
    cloud_cover DOUBLE PRECISION,
    completeness_score DOUBLE PRECISION,
    is_searchable BOOLEAN,
    data_nature TEXT NOT NULL,
    readiness_status TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    PRIMARY KEY (scene_key, event_timestamp)
);

CREATE TABLE IF NOT EXISTS feast.source_vessel_activity (
    vessel_key TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    created_timestamp TIMESTAMPTZ NOT NULL,
    feature_date TEXT NOT NULL,
    transmissions BIGINT,
    active_span_days BIGINT,
    screening_flag BOOLEAN,
    data_nature TEXT NOT NULL,
    readiness_status TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    PRIMARY KEY (vessel_key, event_timestamp)
);

CREATE TABLE IF NOT EXISTS feast.source_air_quality_daily (
    aoi_key TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    created_timestamp TIMESTAMPTZ NOT NULL,
    feature_date TEXT NOT NULL,
    pm25_mean DOUBLE PRECISION,
    pm10_mean DOUBLE PRECISION,
    o3_mean DOUBLE PRECISION,
    station_count BIGINT,
    data_nature TEXT NOT NULL,
    readiness_status TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    PRIMARY KEY (aoi_key, event_timestamp)
);

CREATE TABLE IF NOT EXISTS feast.source_dust_daily (
    aoi_key TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    created_timestamp TIMESTAMPTZ NOT NULL,
    feature_date TEXT NOT NULL,
    aod_mean DOUBLE PRECISION,
    valid_fraction DOUBLE PRECISION,
    wind_speed_mean DOUBLE PRECISION,
    wind_direction_dominant DOUBLE PRECISION,
    data_nature TEXT NOT NULL,
    readiness_status TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    PRIMARY KEY (aoi_key, event_timestamp)
);

ALTER TABLE feast.source_air_quality_daily
    ADD COLUMN IF NOT EXISTS pm25_max DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS pm10_max DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS no2_column_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS so2_column_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS co_column_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS o3_column_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS ch4_column_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS aqi_pm25 DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS aqi_pm10 DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS aqi_band TEXT,
    ADD COLUMN IF NOT EXISTS exceedance_flag BOOLEAN,
    ADD COLUMN IF NOT EXISTS pm25_7d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS pm25_30d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS pm25_change_per_day DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS pm10_7d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS pm10_30d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS pm10_change_per_day DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS days_since_previous_observation BIGINT,
    ADD COLUMN IF NOT EXISTS source_published_at TEXT;

ALTER TABLE feast.source_air_quality_daily
    ALTER COLUMN aqi_band TYPE TEXT USING aqi_band::TEXT;

ALTER TABLE feast.source_dust_daily
    ADD COLUMN IF NOT EXISTS aod_max DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS uv_aerosol_index_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS wind_dir_dominant DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS corridor_aod_max DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS dust_severity_band BIGINT,
    ADD COLUMN IF NOT EXISTS dust_flag BOOLEAN,
    ADD COLUMN IF NOT EXISTS transport_flag BOOLEAN,
    ADD COLUMN IF NOT EXISTS aod_7d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS aod_change_per_day DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS wind_speed_change_per_day DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS days_since_previous_observation BIGINT,
    ADD COLUMN IF NOT EXISTS source_published_at TEXT;

CREATE TABLE IF NOT EXISTS feast.source_climate_indicator_daily (
    aoi_key TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    created_timestamp TIMESTAMPTZ NOT NULL,
    feature_date TEXT NOT NULL,
    lst_c DOUBLE PRECISION,
    lst_anomaly_c DOUBLE PRECISION,
    sst_c DOUBLE PRECISION,
    sst_anomaly_c DOUBLE PRECISION,
    ndvi_mean DOUBLE PRECISION,
    evi_mean DOUBLE PRECISION,
    ndwi_mean DOUBLE PRECISION,
    tree_cover_loss_ha DOUBLE PRECISION,
    desertification_proxy DOUBLE PRECISION,
    lst_anomaly_band BIGINT,
    warming_flag BOOLEAN,
    desertification_flag BOOLEAN,
    lst_anomaly_7d_mean DOUBLE PRECISION,
    lst_anomaly_change_per_day DOUBLE PRECISION,
    ndvi_30d_mean DOUBLE PRECISION,
    ndvi_change_per_day DOUBLE PRECISION,
    days_since_previous_observation BIGINT,
    source_published_at TEXT,
    data_nature TEXT NOT NULL,
    readiness_status TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    PRIMARY KEY (aoi_key, event_timestamp)
);

CREATE TABLE IF NOT EXISTS feast.source_vegetation_health_daily (
    aoi_key TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    created_timestamp TIMESTAMPTZ NOT NULL,
    feature_date TEXT NOT NULL,
    ndvi_mean DOUBLE PRECISION,
    ndvi_max DOUBLE PRECISION,
    evi_mean DOUBLE PRECISION,
    ndvi_trend_30d DOUBLE PRECISION,
    valid_pixel_fraction DOUBLE PRECISION,
    ndvi_health_band BIGINT,
    crop_stress_flag BOOLEAN,
    ndvi_30d_mean DOUBLE PRECISION,
    ndvi_change_per_day DOUBLE PRECISION,
    days_since_previous_observation BIGINT,
    source_published_at TEXT,
    data_nature TEXT NOT NULL,
    readiness_status TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    PRIMARY KEY (aoi_key, event_timestamp)
);
