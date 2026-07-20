"""Generic run-logging client for every pipeline stage
(ingestion/transformation/serving/bi/streaming) plus the batch/streaming/master
roll-ups.

Design (see infrastructure/configs/postgres/init/02-pipeline-run-logging.sql):
  * every stage has a ``metadata.<stage>_run`` header table (one row per DAG
    run) and, for stages that process multiple units, a
    ``metadata.<stage>_run_detail`` table (one row per source/entity/model/
    dataset processed in that run).
  * ``run_id`` is the Airflow ``dag_run_id`` — unique per trigger, threaded
    through every table so a run's whole trail can be queried by one value.
  * All writes are ``INSERT ... ON CONFLICT DO UPDATE`` (idempotent): a retried
    Airflow task re-logging the same ``(run_id, unit_name)`` updates the
    existing row instead of duplicating it.

This module has no Airflow dependency — it is plain psycopg2 + stdlib, unit
tested offline with a fake connection/cursor (see ``pipelines/tests/``).
"""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator

from pipelines.common.db import get_connection

# Stages that only have a header table (their "detail" is the child runs they
# trigger, already logged under those child run_ids). Every other stage
# (ingestion, transformation, serving, bi, streaming) gets a header + detail
# table pair.
_HEADER_ONLY_STAGES = {"master", "batch"}

_VALID_STATUSES = {"RUNNING", "SUCCESS", "FAILED"}


def _table(stage: str, suffix: str = "") -> str:
    """``metadata.<stage>_run`` or ``metadata.<stage>_run_detail``.

    ``stage`` is only ever a hard-coded literal passed by this package's own
    DAGs (never user/request input), so building the identifier this way is
    safe — never accepts external values.
    """
    name = f"{stage}_run{suffix}"
    return f"metadata.{name}"


class StageRunLogger:
    """Logs one pipeline-stage run (e.g. ``ingestion``, ``transformation``,
    ``serving``, ``bi``, ``streaming``) plus its per-unit detail rows."""

    def __init__(
        self,
        stage: str,
        run_id: str,
        *,
        parent_run_id: str | None = None,
        triggered_by: str | None = None,
    ) -> None:
        self.stage = stage
        self.run_id = run_id
        self.parent_run_id = parent_run_id
        self.triggered_by = triggered_by

    # -- header -------------------------------------------------------------
    def start(self) -> None:
        """Create/reset the header row to RUNNING (idempotent on retry)."""
        table = _table(self.stage)
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {table} (run_id, parent_run_id, status, triggered_by, started_at, updated_at)
                VALUES (%s, %s, 'RUNNING', %s, now(), now())
                ON CONFLICT (run_id) DO UPDATE SET
                    status = 'RUNNING',
                    parent_run_id = EXCLUDED.parent_run_id,
                    triggered_by = EXCLUDED.triggered_by,
                    started_at = {table}.started_at,
                    updated_at = now()
                """,
                (self.run_id, self.parent_run_id, self.triggered_by),
            )

    def finish(
        self,
        status: str = "SUCCESS",
        *,
        error: str | None = None,
        extra_columns: dict[str, Any] | None = None,
    ) -> None:
        """Finalize the header row: ended_at=now, status, and (for stages with
        a detail table) total_units/total_rows aggregated from it."""
        assert status in _VALID_STATUSES, f"invalid status {status!r}"
        table = _table(self.stage)
        extra_columns = dict(extra_columns or {})

        total_units: int | None = None
        total_rows: int | None = None
        if self.stage not in _HEADER_ONLY_STAGES:
            detail_table = _table(self.stage, "_detail")
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute(
                    f"SELECT count(*), COALESCE(sum(rows), 0) FROM {detail_table} WHERE run_id = %s",
                    (self.run_id,),
                )
                total_units, total_rows = cur.fetchone()

        set_clauses = [
            "status = %s",
            "ended_at = now()",
            "duration_seconds = EXTRACT(EPOCH FROM (now() - started_at))",
            "error_message = %s",
            "updated_at = now()",
        ]
        params: list[Any] = [status, error]
        if total_units is not None:
            set_clauses.append("total_units = %s")
            params.append(total_units)
        if total_rows is not None:
            set_clauses.append("total_rows = %s")
            params.append(int(total_rows))
        for col, val in extra_columns.items():
            set_clauses.append(f"{col} = %s")
            params.append(val)
        params.append(self.run_id)

        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"UPDATE {table} SET {', '.join(set_clauses)} WHERE run_id = %s",
                params,
            )

    # -- detail rows ----------------------------------------------------------
    def log_unit(
        self,
        unit_name: str,
        *,
        status: str,
        rows: int | None = None,
        duration_seconds: float | None = None,
        error: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Upsert one detail row (source/entity/model/dataset) for this run."""
        assert status in _VALID_STATUSES, f"invalid status {status!r}"
        assert self.stage not in _HEADER_ONLY_STAGES, f"{self.stage} has no detail table"
        table = _table(self.stage, "_detail")
        details_json = json.dumps(details) if details is not None else None

        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {table}
                    (run_id, unit_name, status, started_at, ended_at, duration_seconds, rows, error_message, details, updated_at)
                VALUES
                    (%s, %s, %s, now() - make_interval(secs => %s), now(), %s, %s, %s, %s::jsonb, now())
                ON CONFLICT (run_id, unit_name) DO UPDATE SET
                    status = EXCLUDED.status,
                    ended_at = EXCLUDED.ended_at,
                    duration_seconds = EXCLUDED.duration_seconds,
                    rows = EXCLUDED.rows,
                    error_message = EXCLUDED.error_message,
                    details = EXCLUDED.details,
                    updated_at = now()
                """,
                (
                    self.run_id,
                    unit_name,
                    status,
                    duration_seconds or 0,
                    duration_seconds,
                    rows,
                    error,
                    details_json,
                ),
            )


@contextmanager
def timed(logger: StageRunLogger, unit_name: str) -> Iterator[dict[str, Any]]:
    """Time a block of work and log a detail row for it. Yields a mutable
    ``result`` dict the caller should populate with at least ``rows`` (and any
    other JSON-serialisable keys, kept as ``details``). Logs FAILED (with the
    exception message) and re-raises on error, so the Airflow task still fails.

    Usage::

        with timed(logger, "SWPC") as result:
            out = run_connector_to_bronze(SwpcConnector())
            result["rows"] = out["records"]
            result.update(out)
    """
    result: dict[str, Any] = {}
    start = time.monotonic()
    try:
        yield result
    except Exception as exc:  # noqa: BLE001 - re-raised after logging
        duration = time.monotonic() - start
        logger.log_unit(unit_name, status="FAILED", duration_seconds=duration, error=str(exc))
        raise
    else:
        duration = time.monotonic() - start
        rows = result.pop("rows", None)
        logger.log_unit(unit_name, status="SUCCESS", rows=rows, duration_seconds=duration, details=result or None)


def run_logged(
    logger: StageRunLogger,
    unit_name: str,
    fn: Callable[[], dict[str, Any]],
    *,
    rows_key: str = "rows",
) -> dict[str, Any]:
    """Run ``fn()`` (expected to return a JSON-serialisable dict containing
    ``rows_key``), log a SUCCESS/FAILED detail row, and return the result
    (re-raising on failure so the Airflow task fails too)."""
    with timed(logger, unit_name) as result:
        out = fn()
        result["rows"] = out.get(rows_key)
        result.update(out)
        return out
