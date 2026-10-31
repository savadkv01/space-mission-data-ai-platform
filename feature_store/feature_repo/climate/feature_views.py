from datetime import timedelta

from feast import FeatureView, Field
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import (
    PostgreSQLSource,
)
from feast.types import Bool, Float32, Int64, String

from entities import aoi


def _source(table: str) -> PostgreSQLSource:
    return PostgreSQLSource(
        name=f"{table}_source",
        query=f"SELECT * FROM feast.{table}",
        timestamp_field="event_timestamp",
        created_timestamp_column="created_timestamp",
    )


def _meta_fields() -> list[Field]:
    return [
        Field(name="feature_date", dtype=String),
        Field(name="source_published_at", dtype=String),
        Field(name="data_nature", dtype=String),
        Field(name="readiness_status", dtype=String),
    ]


air_quality_aoi_daily = FeatureView(
    name="air_quality_aoi_daily",
    entities=[aoi],
    ttl=timedelta(days=2),
    schema=[
        Field(name="pm25_mean", dtype=Float32),
        Field(name="pm25_max", dtype=Float32),
        Field(name="pm10_mean", dtype=Float32),
        Field(name="pm10_max", dtype=Float32),
        Field(name="no2_column_mean", dtype=Float32),
        Field(name="so2_column_mean", dtype=Float32),
        Field(name="co_column_mean", dtype=Float32),
        Field(name="o3_column_mean", dtype=Float32),
        Field(name="ch4_column_mean", dtype=Float32),
        Field(name="station_count", dtype=Int64),
        Field(name="aqi_pm25", dtype=Float32),
        Field(name="aqi_pm10", dtype=Float32),
        Field(name="aqi_band", dtype=String),
        Field(name="exceedance_flag", dtype=Bool),
        Field(name="pm25_7d_mean", dtype=Float32),
        Field(name="pm25_30d_mean", dtype=Float32),
        Field(name="pm25_change_per_day", dtype=Float32),
        Field(name="pm10_7d_mean", dtype=Float32),
        Field(name="pm10_30d_mean", dtype=Float32),
        Field(name="pm10_change_per_day", dtype=Float32),
        Field(name="days_since_previous_observation", dtype=Int64),
        *_meta_fields(),
    ],
    source=_source("source_air_quality_daily"),
    tags={"readiness": "blocked", "use": "not_available"},
    description=(
        "AOI/day pollutants and AQI from the Phase 11b serving product. "
        "CH4 remains null until the serving contract provides it."
    ),
)

dust_aoi_daily = FeatureView(
    name="dust_aoi_daily",
    entities=[aoi],
    ttl=timedelta(days=7),
    schema=[
        Field(name="aod_mean", dtype=Float32),
        Field(name="aod_max", dtype=Float32),
        Field(name="uv_aerosol_index_mean", dtype=Float32),
        Field(name="wind_speed_mean", dtype=Float32),
        Field(name="wind_dir_dominant", dtype=Float32),
        Field(name="corridor_aod_max", dtype=Float32),
        Field(name="valid_fraction", dtype=Float32),
        Field(name="dust_severity_band", dtype=Int64),
        Field(name="dust_flag", dtype=Bool),
        Field(name="transport_flag", dtype=Bool),
        Field(name="aod_7d_mean", dtype=Float32),
        Field(name="aod_change_per_day", dtype=Float32),
        Field(name="wind_speed_change_per_day", dtype=Float32),
        Field(name="days_since_previous_observation", dtype=Int64),
        *_meta_fields(),
    ],
    source=_source("source_dust_daily"),
    tags={"readiness": "blocked", "use": "not_available"},
    description=(
        "AOI/day aerosol and dust flags with NASA POWER wind context. "
        "No transport score is inferred from missing wind observations."
    ),
)

climate_indicator_aoi_daily = FeatureView(
    name="climate_indicator_aoi_daily",
    entities=[aoi],
    ttl=timedelta(days=45),
    schema=[
        Field(name="lst_c", dtype=Float32),
        Field(name="lst_anomaly_c", dtype=Float32),
        Field(name="sst_c", dtype=Float32),
        Field(name="sst_anomaly_c", dtype=Float32),
        Field(name="ndvi_mean", dtype=Float32),
        Field(name="evi_mean", dtype=Float32),
        Field(name="ndwi_mean", dtype=Float32),
        Field(name="tree_cover_loss_ha", dtype=Float32),
        Field(name="desertification_proxy", dtype=Float32),
        Field(name="lst_anomaly_band", dtype=Int64),
        Field(name="warming_flag", dtype=Bool),
        Field(name="desertification_flag", dtype=Bool),
        Field(name="lst_anomaly_7d_mean", dtype=Float32),
        Field(name="lst_anomaly_change_per_day", dtype=Float32),
        Field(name="ndvi_30d_mean", dtype=Float32),
        Field(name="ndvi_change_per_day", dtype=Float32),
        Field(name="days_since_previous_observation", dtype=Int64),
        *_meta_fields(),
    ],
    source=_source("source_climate_indicator_daily"),
    tags={"readiness": "blocked", "use": "not_available"},
    description=(
        "AOI/day climate indicators from the Phase 11b serving product, subject "
        "to the feature-store readiness gate."
    ),
)

vegetation_health_aoi_daily = FeatureView(
    name="vegetation_health_aoi_daily",
    entities=[aoi],
    ttl=timedelta(days=45),
    schema=[
        Field(name="ndvi_mean", dtype=Float32),
        Field(name="ndvi_max", dtype=Float32),
        Field(name="evi_mean", dtype=Float32),
        Field(name="ndvi_trend_30d", dtype=Float32),
        Field(name="valid_pixel_fraction", dtype=Float32),
        Field(name="ndvi_health_band", dtype=Int64),
        Field(name="crop_stress_flag", dtype=Bool),
        Field(name="ndvi_30d_mean", dtype=Float32),
        Field(name="ndvi_change_per_day", dtype=Float32),
        Field(name="days_since_previous_observation", dtype=Int64),
        *_meta_fields(),
    ],
    source=_source("source_vegetation_health_daily"),
    tags={"readiness": "blocked", "use": "not_available"},
    description="AOI/day vegetation features from the Phase 11b serving product.",
)
