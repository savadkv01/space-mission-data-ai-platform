"""Centralised, environment-driven configuration for the ingestion layer.

All runtime endpoints, credentials, topic names, and bucket names are read from
the environment (loaded from ``infrastructure/env/.env`` or a local ``.env``).
No secrets are hard-coded. Import :data:`settings` everywhere instead of reading
``os.environ`` directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Resolve the platform .env (infra) first, then a local override if present.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_INFRA_ENV = _REPO_ROOT / "infrastructure" / "env" / ".env"
_LOCAL_ENV = Path(__file__).resolve().parents[1] / ".env"

for _candidate in (_INFRA_ENV, _LOCAL_ENV):
    if _candidate.exists():
        load_dotenv(_candidate, override=False)


def _get(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else default


@dataclass(frozen=True)
class KafkaSettings:
    bootstrap_servers: str = field(default_factory=lambda: _get("KAFKA_BOOTSTRAP", "localhost:9092"))
    client_id: str = "space-ingestion"
    # Topic catalogue (Task 2 — topic strategy)
    topic_telemetry_raw: str = "telemetry.satellite.raw"
    topic_telemetry_cleaned: str = "telemetry.satellite.cleaned"
    topic_telemetry_dlq: str = "telemetry.satellite.dlq"
    topic_space_weather: str = "space.weather.events"
    topic_launch_events: str = "launch.events"
    topic_orbit_stream: str = "orbit.position.stream"
    num_partitions: int = field(default_factory=lambda: int(_get("KAFKA_NUM_PARTITIONS", "3")))
    replication_factor: int = 1

    @property
    def all_topics(self) -> dict[str, int]:
        """Topic name -> partition count (DLQ kept single-partition)."""
        return {
            self.topic_telemetry_raw: self.num_partitions,
            self.topic_telemetry_cleaned: self.num_partitions,
            self.topic_telemetry_dlq: 1,
            self.topic_space_weather: 1,
            self.topic_launch_events: 1,
            self.topic_orbit_stream: self.num_partitions,
        }


@dataclass(frozen=True)
class MinioSettings:
    endpoint: str = field(default_factory=lambda: _get("MINIO_ENDPOINT", "http://localhost:9000"))
    access_key: str = field(default_factory=lambda: _get("MINIO_ROOT_USER", "platform_minio"))
    secret_key: str = field(default_factory=lambda: _get("MINIO_ROOT_PASSWORD", ""))
    region: str = field(default_factory=lambda: _get("AWS_REGION", "us-east-1"))
    bucket_bronze: str = "bronze"
    bucket_staging: str = "staging"


@dataclass(frozen=True)
class DatasetCredentials:
    nasa_api_key: str = field(default_factory=lambda: _get("NASA_API_KEY", "DEMO_KEY"))
    firms_map_key: str = field(default_factory=lambda: _get("FIRMS_MAP_KEY"))
    gfw_api_token: str = field(default_factory=lambda: _get("GFW_API_TOKEN"))
    sentinelhub_client_id: str = field(default_factory=lambda: _get("SENTINELHUB_CLIENT_ID"))
    sentinelhub_client_secret: str = field(default_factory=lambda: _get("SENTINELHUB_CLIENT_SECRET"))
    openaq_api_key: str = field(default_factory=lambda: _get("OPENAQ_API_KEY"))
    # Google Earth Engine (free S-5P / MODIS AOD backend; service-account auth).
    gee_project: str = field(default_factory=lambda: _get("GEE_PROJECT"))
    gee_service_account: str = field(default_factory=lambda: _get("GEE_SERVICE_ACCOUNT"))
    gee_key_file: str = field(default_factory=lambda: _get("GEE_KEY_FILE"))


@dataclass(frozen=True)
class ClimateSettings:
    """AOIs and source parameter lists for the climate / dust / air-quality track.

    Bounding boxes are ``[min_lon, min_lat, max_lon, max_lat]`` (EPSG:4326),
    sourced from Phase 5b (docs/source-data-analysis/climate/02-aoi-strategy.md).
    AOI clipping is mandatory to respect the 16 GB budget and Sentinel Hub
    Processing-Unit quota; all atmospheric requests are AOI-bounded.
    """

    #: Named AOI bounding boxes: UAE-GULF primary + dust corridors, and the
    #: INDIA regional tier (docs/source-data-analysis/climate/02-aoi-strategy.md).
    aois: dict[str, tuple[float, float, float, float]] = field(default_factory=lambda: {
        "AOI-UAE-NAT": (51.0, 22.5, 56.5, 26.2),
        "AOI-AUH": (53.3, 23.5, 55.3, 24.7),
        "AOI-DXB": (54.9, 24.8, 55.6, 25.4),
        "AOI-COAST": (51.5, 24.0, 56.4, 26.1),
        "AOI-DESERT": (52.0, 22.5, 55.5, 23.8),
        "AOI-ARABIA": (42.0, 18.0, 55.0, 30.0),
        "AOI-IRAQ": (42.0, 29.0, 48.5, 36.0),
        "AOI-IRAN": (47.0, 28.0, 55.0, 34.0),
        "AOI-GULF": (48.0, 24.0, 57.0, 30.5),
        "IN-DEL-NCR": (76.8, 28.3, 77.6, 28.9),
        "IN-MUM": (72.75, 18.85, 73.2, 19.35),
        "IN-PB-HR": (73.8, 29.0, 77.4, 32.5),
        "IN-THAR": (69.5, 24.5, 74.5, 29.0),
        "IN-GUJ-COAST": (68.5, 20.0, 73.0, 24.0),
        "IN-ASSAM": (89.7, 25.8, 96.0, 27.9),
    })
    #: Analysis region per AOI. Rollups, dust corridors, AQI standards and fire
    #: freshness never combine AOIs from different regions.
    aoi_regions: dict[str, str] = field(default_factory=lambda: {
        **{aoi: "UAE-GULF" for aoi in (
            "AOI-UAE-NAT", "AOI-AUH", "AOI-DXB", "AOI-COAST", "AOI-DESERT",
            "AOI-ARABIA", "AOI-IRAQ", "AOI-IRAN", "AOI-GULF")},
        **{aoi: "INDIA" for aoi in (
            "IN-DEL-NCR", "IN-MUM", "IN-PB-HR", "IN-THAR", "IN-GUJ-COAST", "IN-ASSAM")},
    })
    #: Per-region, per-source AOI plans (keeps request volume within the laptop
    #: and provider budgets; OpenAQ in INDIA is PM-only).
    region_sources: dict[str, dict[str, tuple[str, ...]]] = field(default_factory=lambda: {
        "UAE-GULF": {
            # Maritime activity only; other UAE-GULF sources keep their own loops
            # in run_full_batch_ingest.
            "gfw": ("AOI-GULF", "AOI-COAST"),
        },
        "INDIA": {
            "firms": ("IN-PB-HR", "IN-DEL-NCR", "IN-THAR", "IN-GUJ-COAST", "IN-ASSAM"),
            "openaq": ("IN-DEL-NCR", "IN-MUM"),
            "tropomi": ("IN-DEL-NCR", "IN-PB-HR"),
            "aod": ("IN-THAR", "IN-GUJ-COAST", "IN-DEL-NCR", "IN-PB-HR"),
            "ndvi": ("IN-PB-HR",),
            "ndwi": ("IN-ASSAM",),
            "gfw": ("IN-GUJ-COAST", "IN-MUM"),
        },
    })
    #: GFW 4Wings look-back (days ending yesterday); rows are AOI x day x flag.
    gfw_lookback_days: int = 30
    #: OpenAQ PM-only parameter list for high-density station regions.
    openaq_pm_pollutants: tuple[str, ...] = ("pm25", "pm10")
    #: Fixed per-request FIRMS detection cap; truncation is reported as capped coverage.
    firms_max_records_per_request: int = 10000
    #: FIRMS product for all regions. VIIRS S-NPP NRT ends 2026-11-02 at FIRMS
    #: (data_availability API), so the live feed is VIIRS NOAA-20 (same 375 m
    #: VIIRS I-band fields). One sensor per day avoids double counting, as the
    #: satellite is part of the Silver fire key.
    firms_source: str = field(default_factory=lambda: _get("FIRMS_SOURCE", "VIIRS_NOAA20_NRT"))
    #: OpenAQ ground-station pollutants (canonical lowercase parameter codes).
    openaq_pollutants: tuple[str, ...] = ("pm25", "pm10", "o3", "no2", "co", "so2")
    #: TROPOMI (Sentinel-5P) products via the Sentinel Hub Statistical API.
    tropomi_products: tuple[str, ...] = ("NO2", "SO2", "CO", "O3", "CH4", "AER_AI")

    def bbox(self, aoi_id: str) -> list[float]:
        """Return the bounding box for ``aoi_id`` as a mutable list."""
        if aoi_id not in self.aois:
            raise KeyError(f"unknown AOI {aoi_id!r}; choose from {sorted(self.aois)}")
        return list(self.aois[aoi_id])

    def firms_area(self, aoi_id: str) -> str:
        """FIRMS ``west,south,east,north`` area string for ``aoi_id``."""
        return ",".join(str(v) for v in self.bbox(aoi_id))


@dataclass(frozen=True)
class Settings:
    env: str = field(default_factory=lambda: _get("INGESTION_ENV", "local"))
    log_level: str = field(default_factory=lambda: _get("LOG_LEVEL", "INFO"))
    kafka: KafkaSettings = field(default_factory=KafkaSettings)
    minio: MinioSettings = field(default_factory=MinioSettings)
    credentials: DatasetCredentials = field(default_factory=DatasetCredentials)
    climate: ClimateSettings = field(default_factory=ClimateSettings)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
