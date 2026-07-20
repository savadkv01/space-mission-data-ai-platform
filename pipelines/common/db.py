"""PostgreSQL connection helper for the pipelines/run-logging layer.

``psycopg2`` is imported lazily so the rest of the ``pipelines`` package (and
its unit tests) import cleanly in environments without it installed — mirrors
the ``boto3``/``pyspark`` lazy-import convention already used in
``ingestion/common/minio_io.py`` and ``transformation/common/spark.py``.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from pipelines.config.settings import settings


@contextmanager
def get_connection() -> Iterator[Any]:
    """Yield a psycopg2 connection to the shared platform PostgreSQL instance,
    with ``search_path`` defaulted to the ``metadata`` schema. Commits on
    success, rolls back on exception, always closes."""
    import psycopg2  # lazy import

    conn = psycopg2.connect(settings.postgres.dsn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
