"""Centralised, environment-driven configuration for the pipelines/orchestration
layer (run-logging Postgres connection + Superset BI-refresh endpoint).

Mirrors the conventions in ``ingestion/config/settings.py`` /
``transformation/config/settings.py``: read from the environment (loaded from
``infrastructure/env/.env``), no hard-coded secrets, import :data:`settings`
everywhere instead of reading ``os.environ`` directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[2]
_INFRA_ENV = _REPO_ROOT / "infrastructure" / "env" / ".env"

if _INFRA_ENV.exists():
    load_dotenv(_INFRA_ENV, override=False)


def _get(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else default


@dataclass(frozen=True)
class PostgresSettings:
    """Connection to the shared platform PostgreSQL instance (ADR-007);
    run-logging tables live in the ``metadata`` schema."""

    host: str = field(default_factory=lambda: _get("POSTGRES_HOST", "postgres"))
    port: int = field(default_factory=lambda: int(_get("POSTGRES_PORT", "5432")))
    database: str = field(default_factory=lambda: _get("POSTGRES_DB", "platform"))
    user: str = field(default_factory=lambda: _get("POSTGRES_USER", "platform"))
    password: str = field(default_factory=lambda: _get("POSTGRES_PASSWORD", ""))
    schema: str = "metadata"

    @property
    def dsn(self) -> str:
        return (
            f"host={self.host} port={self.port} dbname={self.database} "
            f"user={self.user} password={self.password} options=-csearch_path={self.schema}"
        )


@dataclass(frozen=True)
class SupersetSettings:
    """Superset REST API, used by the BI-refresh pipeline stage."""

    base_url: str = field(default_factory=lambda: _get("SUPERSET_INTERNAL_URL", "http://superset:8088"))
    admin_user: str = field(default_factory=lambda: _get("SUPERSET_ADMIN_USER", "admin"))
    admin_password: str = field(default_factory=lambda: _get("SUPERSET_ADMIN_PASSWORD", ""))


@dataclass(frozen=True)
class MinioSettings:
    endpoint: str = field(default_factory=lambda: _get("MINIO_ENDPOINT", "http://localhost:9000"))
    access_key: str = field(default_factory=lambda: _get("MINIO_ROOT_USER", "platform_minio"))
    secret_key: str = field(default_factory=lambda: _get("MINIO_ROOT_PASSWORD", ""))


@dataclass(frozen=True)
class Settings:
    log_level: str = field(default_factory=lambda: _get("LOG_LEVEL", "INFO"))
    postgres: PostgresSettings = field(default_factory=PostgresSettings)
    superset: SupersetSettings = field(default_factory=SupersetSettings)
    minio: MinioSettings = field(default_factory=MinioSettings)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
