"""Environment-driven configuration for the transformation layer.

Mirrors the ingestion layer's pattern: endpoints, bucket/layer names, and Spark
tuning are read from the environment (``infrastructure/env/.env`` or a local
``.env``). No secrets are hard-coded. Import :data:`settings` everywhere instead
of reading ``os.environ`` directly.

The defaults are deliberately sized for a 16 GB laptop running Spark in local
mode (see ``common/spark.py``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

try:  # dotenv is optional for pure-Python/offline use
    from dotenv import load_dotenv
except Exception:  # noqa: BLE001
    def load_dotenv(*_args, **_kwargs):  # type: ignore
        return False


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
class LakeSettings:
    """Object-store layer locations. URIs are backend-agnostic (MinIO/S3/local)."""

    endpoint: str = field(default_factory=lambda: _get("MINIO_ENDPOINT", "http://localhost:9000"))
    access_key: str = field(default_factory=lambda: _get("MINIO_ROOT_USER", "platform_minio"))
    secret_key: str = field(default_factory=lambda: _get("MINIO_ROOT_PASSWORD", ""))
    region: str = field(default_factory=lambda: _get("AWS_REGION", "us-east-1"))
    bucket_bronze: str = "bronze"
    bucket_silver: str = "silver"
    bucket_gold: str = "gold"
    bucket_features: str = "features"
    bucket_quarantine: str = "quarantine"

    def path(self, layer: str, dataset: str) -> str:
        bucket = getattr(self, f"bucket_{layer}", layer)
        return f"s3a://{bucket}/{dataset}"


@dataclass(frozen=True)
class SparkSettings:
    app_name: str = "space-transformation"
    master: str = field(default_factory=lambda: _get("SPARK_MASTER", "local[*]"))
    # 16 GB-laptop-friendly defaults; overridable via env.
    driver_memory: str = field(default_factory=lambda: _get("SPARK_DRIVER_MEMORY", "2g"))
    executor_memory: str = field(default_factory=lambda: _get("SPARK_EXECUTOR_MEMORY", "2g"))
    shuffle_partitions: int = field(default_factory=lambda: int(_get("SPARK_SHUFFLE_PARTITIONS", "8")))
    checkpoint_dir: str = field(default_factory=lambda: _get("SPARK_CHECKPOINT_DIR", "/tmp/spark-checkpoints"))


@dataclass(frozen=True)
class StreamingSettings:
    bootstrap_servers: str = field(default_factory=lambda: _get("KAFKA_BOOTSTRAP", "localhost:9092"))
    topic_telemetry_cleaned: str = "telemetry.satellite.cleaned"
    topic_orbit_stream: str = "orbit.position.stream"
    topic_space_weather: str = "space.weather.events"
    # Watermark / window tuning (Task 5).
    watermark_delay: str = "2 minutes"
    window_duration: str = "1 minute"
    slide_duration: str = "30 seconds"
    trigger_interval: str = "30 seconds"


@dataclass(frozen=True)
class Settings:
    env: str = field(default_factory=lambda: _get("TRANSFORM_ENV", "local"))
    log_level: str = field(default_factory=lambda: _get("LOG_LEVEL", "INFO"))
    lake: LakeSettings = field(default_factory=LakeSettings)
    spark: SparkSettings = field(default_factory=SparkSettings)
    streaming: StreamingSettings = field(default_factory=StreamingSettings)
    # Local working dir for offline demo output (no object store required).
    local_output: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1] / "output")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
