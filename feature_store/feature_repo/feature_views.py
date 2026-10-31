from datetime import timedelta

from feast import FeatureService, FeatureView, Field
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import (
    PostgreSQLSource,
)
from feast.types import Bool, Float32, Int64, String

from climate.feature_views import (
    air_quality_aoi_daily,
    climate_indicator_aoi_daily,
    dust_aoi_daily,
    vegetation_health_aoi_daily,
)
from entities import (
    aoi,
    launch_provider,
    mission,
    satellite,
    scene,
    vessel,
    weather_scope,
)


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
        Field(name="data_nature", dtype=String),
        Field(name="readiness_status", dtype=String),
    ]


satellite_health_daily = FeatureView(
    name="satellite_health_daily",
    entities=[satellite],
    ttl=timedelta(days=14),
    schema=[
        Field(name="samples", dtype=Int64),
        Field(name="anomaly_samples", dtype=Int64),
        Field(name="anomaly_density", dtype=Float32),
        Field(name="health_score", dtype=Float32),
        Field(name="battery_voltage_drift", dtype=Float32),
        *_meta_fields(),
    ],
    source=_source("source_satellite_health"),
    tags={"readiness": "demo_only", "use": "pipeline_validation"},
    description="Synthetic satellite-health demonstrator; never operational evidence.",
)

mission_operations = FeatureView(
    name="mission_operations",
    entities=[mission],
    ttl=timedelta(days=14),
    schema=[
        Field(name="uptime_fraction", dtype=Float32),
        Field(name="anomaly_count", dtype=Int64),
        Field(name="operational_state", dtype=String),
        *_meta_fields(),
    ],
    source=_source("source_mission_operations"),
    tags={"readiness": "blocked", "use": "not_available"},
)

orbit_stability = FeatureView(
    name="orbit_stability",
    entities=[satellite],
    ttl=timedelta(days=7),
    schema=[
        Field(name="altitude_drift_km", dtype=Float32),
        Field(name="velocity_variance_km2_s2", dtype=Float32),
        Field(name="decay_rate_km_day", dtype=Float32),
        *_meta_fields(),
    ],
    source=_source("source_orbit_stability"),
    tags={"readiness": "blocked", "use": "not_available"},
)

launch_performance_monthly = FeatureView(
    name="launch_performance_monthly",
    entities=[launch_provider],
    ttl=timedelta(days=400),
    schema=[
        Field(name="launches", dtype=Int64),
        Field(name="success_rate", dtype=Float32),
        Field(name="cadence_per_month", dtype=Float32),
        Field(name="mean_delay_days", dtype=Float32),
        *_meta_fields(),
    ],
    source=_source("source_launch_performance"),
    tags={"readiness": "blocked", "use": "not_available"},
)

space_weather_daily = FeatureView(
    name="space_weather_daily",
    entities=[weather_scope],
    ttl=timedelta(days=7),
    schema=[
        Field(name="max_kp_index", dtype=Float32),
        Field(name="mean_kp_index", dtype=Float32),
        Field(name="storm_events", dtype=Int64),
        *_meta_fields(),
    ],
    source=_source("source_space_weather"),
    tags={"readiness": "blocked", "use": "not_available"},
    description="Candidate weather measures only; source state and telemetry linkage require review.",
)

wildfire_aoi_daily = FeatureView(
    name="wildfire_aoi_daily",
    entities=[aoi],
    ttl=timedelta(days=30),
    schema=[
        Field(name="detections", dtype=Int64),
        Field(name="mean_frp", dtype=Float32),
        Field(name="max_frp", dtype=Float32),
        Field(name="ems_corroborated", dtype=Bool),
        Field(name="area_km2", dtype=Float32),
        *_meta_fields(),
    ],
    source=_source("source_wildfire_aoi_daily"),
    tags={"readiness": "blocked", "use": "not_available"},
    description="AOI daily summary; blocked until all source detections reconcile to matched or unmatched.",
)

spectral_index_daily = FeatureView(
    name="spectral_index_daily",
    entities=[aoi],
    ttl=timedelta(days=30),
    schema=[
        Field(name="ndvi_mean", dtype=Float32),
        Field(name="ndwi_mean", dtype=Float32),
        Field(name="nbr_mean", dtype=Float32),
        Field(name="valid_pixel_fraction", dtype=Float32),
        *_meta_fields(),
    ],
    source=_source("source_spectral_index_daily"),
    tags={"readiness": "blocked", "use": "not_available"},
    description="Requires non-empty, provenance-backed spectral-index inputs.",
)

scene_catalog_metadata = FeatureView(
    name="scene_catalog_metadata",
    entities=[scene],
    ttl=timedelta(days=90),
    schema=[
        Field(name="cloud_cover", dtype=Float32),
        Field(name="completeness_score", dtype=Float32),
        Field(name="is_searchable", dtype=Bool),
        *_meta_fields(),
    ],
    source=_source("source_scene_catalog"),
    tags={"readiness": "restricted", "use": "catalog_discovery_only"},
    description="Scene-catalog metadata for discovery; not imagery or a validated EO result.",
)

vessel_activity_daily = FeatureView(
    name="vessel_activity_daily",
    entities=[vessel],
    ttl=timedelta(days=14),
    schema=[
        Field(name="transmissions", dtype=Int64),
        Field(name="active_span_days", dtype=Int64),
        Field(name="screening_flag", dtype=Bool),
        *_meta_fields(),
    ],
    source=_source("source_vessel_activity"),
    tags={"readiness": "blocked", "use": "not_available"},
    description="Heuristic screening is not a confirmed event or behavioral finding.",
)

FEATURE_VIEWS = [
    satellite_health_daily,
    mission_operations,
    orbit_stability,
    launch_performance_monthly,
    space_weather_daily,
    wildfire_aoi_daily,
    spectral_index_daily,
    scene_catalog_metadata,
    vessel_activity_daily,
    air_quality_aoi_daily,
    dust_aoi_daily,
    climate_indicator_aoi_daily,
    vegetation_health_aoi_daily,
]

FEATURE_SERVICES = [
    FeatureService(
        name="satellite_health_demo_service",
        features=[satellite_health_daily],
        tags={"readiness": "demo_only"},
    ),
    FeatureService(
        name="eo_scene_discovery_service",
        features=[scene_catalog_metadata],
        tags={"readiness": "restricted"},
    ),
    FeatureService(
        name="climate_dust_training_service",
        features=[
            wildfire_aoi_daily,
            air_quality_aoi_daily,
            dust_aoi_daily,
            climate_indicator_aoi_daily,
            vegetation_health_aoi_daily,
        ],
        tags={"readiness": "blocked_until_source_promotion"},
    ),
]
