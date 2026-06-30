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


@dataclass(frozen=True)
class Settings:
    env: str = field(default_factory=lambda: _get("INGESTION_ENV", "local"))
    log_level: str = field(default_factory=lambda: _get("LOG_LEVEL", "INFO"))
    kafka: KafkaSettings = field(default_factory=KafkaSettings)
    minio: MinioSettings = field(default_factory=MinioSettings)
    credentials: DatasetCredentials = field(default_factory=DatasetCredentials)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
