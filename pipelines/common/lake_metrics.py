"""Row-count helpers used by the transformation/serving pipeline stages to log
``rows`` on each detail row, without needing Spark/dbt installed in the Airflow
container. DuckDB's ``httpfs`` extension queries Parquet directly from MinIO
(same technique as ``transformation/scripts/query_gold.py`` /
``query_stream.py``); the ``duckdb`` package itself is pure-Python/C, so it is
a lightweight addition to the Airflow image (see ``airflow.Dockerfile``).
"""

from __future__ import annotations

from urllib.parse import urlparse

from pipelines.config.settings import settings


def _minio_host_port() -> str:
    """``http://minio:9000`` -> ``minio:9000`` (duckdb's s3_endpoint wants no scheme)."""
    parsed = urlparse(settings.minio.endpoint)
    return parsed.netloc or parsed.path


def _configure_httpfs(con) -> None:
    con.execute("install httpfs; load httpfs;")
    con.execute(f"set s3_endpoint='{_minio_host_port()}';")
    con.execute("set s3_use_ssl=false;")
    con.execute("set s3_url_style='path';")
    con.execute(f"set s3_access_key_id='{settings.minio.access_key}';")
    con.execute(f"set s3_secret_access_key='{settings.minio.secret_key}';")


def _duckdb_connection():
    import duckdb  # lazy import

    con = duckdb.connect()
    _configure_httpfs(con)
    return con


def count_parquet_rows(s3_glob: str) -> int:
    """Row count for a Parquet dataset in MinIO, e.g. ``s3://silver/silver_fire/*.parquet``.

    Returns 0 (rather than raising) if the path doesn't exist yet — a Spark job
    that produced zero rows still writes a schema-only Parquet part, but a job
    that hasn't run at all yet legitimately has no path to read.
    """
    con = _duckdb_connection()
    try:
        row = con.execute(f"select count(*) from read_parquet('{s3_glob}')").fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0
    finally:
        con.close()


def stream_window_anomaly_summary(s3_glob: str) -> dict[str, int]:
    """Totals for the windowed streaming sink (``samples`` / ``anomaly_samples``).

    ``mixed_windows`` counts windows whose anomaly count is neither 0 nor equal to
    ``samples``; with an all-anomalous wave followed by an all-nominal wave far
    enough apart, every flushed window must be pure. Raises if unreadable, so a
    missing sink cannot masquerade as "no anomalies".
    """
    con = _duckdb_connection()
    try:
        row = con.execute(
            "select count(*), coalesce(sum(samples), 0), coalesce(sum(anomaly_samples), 0), "
            "coalesce(sum(case when anomaly_samples not in (0, samples) then 1 else 0 end), 0) "
            f"from read_parquet('{s3_glob}')"
        ).fetchone()
    finally:
        con.close()
    windows, samples, anomalies, mixed = (int(v) for v in row)
    return {"windows": windows, "samples": samples, "anomaly_samples": anomalies,
            "mixed_windows": mixed}


def count_duckdb_table_rows(db_path: str, qualified_table: str) -> int:
    """Row count for a table/view in a local DuckDB file, e.g. the serving
    warehouse (``serving.serving_wildfire_daily``). Read-only, non-destructive."""
    import duckdb  # lazy import

    con = duckdb.connect(db_path, read_only=True)
    try:
        _configure_httpfs(con)
        schema, separator, table = qualified_table.partition(".")
        if not separator or not schema or not table or "." in table:
            raise ValueError(f"Expected a schema-qualified table name, got {qualified_table!r}")

        catalog_row = con.execute("select current_database()").fetchone()
        if catalog_row is None:
            raise RuntimeError("DuckDB did not report the connected database name")

        full_name = ".".join(
            '"' + str(identifier).replace('"', '""') + '"'
            for identifier in (catalog_row[0], schema, table)
        )
        row = con.execute(f"select count(*) from {full_name}").fetchone()
        if row is None:
            raise RuntimeError(f"DuckDB returned no count for {qualified_table!r}")
        return int(row[0])
    finally:
        con.close()
