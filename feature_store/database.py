from __future__ import annotations

import os
from pathlib import Path

import psycopg
from sqlalchemy.engine import URL


def connect() -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=5,
    )


def configure_registry_url() -> str:
    url = URL.create(
        drivername="postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=os.environ["POSTGRES_DB"],
        query={"options": "-csearch_path=feast"},
    ).render_as_string(hide_password=False)
    os.environ["FEAST_REGISTRY_URL"] = url
    return url


def initialize_source_tables() -> None:
    sql_path = Path(__file__).parent / "sql" / "01-feature-sources.sql"
    with connect() as connection:
        connection.execute(sql_path.read_text(encoding="utf-8"))
