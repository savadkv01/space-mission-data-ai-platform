"""Offline unit tests for pipelines.common.run_logger — no real Postgres or
Airflow needed. A fake connection/cursor records every executed statement so
we can assert on SQL shape + params without a database."""

from __future__ import annotations

import json
from contextlib import contextmanager

import pytest

from pipelines.common import run_logger as rl


class _FakeCursor:
    def __init__(self, fetch_result=None):
        self.executed: list[tuple[str, tuple]] = []
        self._fetch_result = fetch_result

    def execute(self, sql, params=None):
        self.executed.append((" ".join(sql.split()), tuple(params) if params else ()))

    def fetchone(self):
        return self._fetch_result

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConnection:
    def __init__(self, cursor: _FakeCursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


@pytest.fixture
def fake_db(monkeypatch):
    cursor = _FakeCursor(fetch_result=(3, 42))  # total_units=3, total_rows=42

    @contextmanager
    def _fake_get_connection():
        yield _FakeConnection(cursor)

    monkeypatch.setattr(rl, "get_connection", _fake_get_connection)
    return cursor


def test_start_inserts_running_header(fake_db):
    logger = rl.StageRunLogger("ingestion", "run-123", parent_run_id="batch-1", triggered_by="airflow")
    logger.start()

    sql, params = fake_db.executed[-1]
    assert "INSERT INTO metadata.ingestion_run" in sql
    assert "ON CONFLICT (run_id) DO UPDATE" in sql
    assert params == ("run-123", "batch-1", "airflow")


def test_log_unit_upserts_detail_row(fake_db):
    logger = rl.StageRunLogger("ingestion", "run-123")
    logger.log_unit("SWPC", status="SUCCESS", rows=57, duration_seconds=1.5, details={"batch_id": "abc"})

    sql, params = fake_db.executed[-1]
    assert "INSERT INTO metadata.ingestion_run_detail" in sql
    assert "ON CONFLICT (run_id, unit_name) DO UPDATE" in sql
    assert params[0] == "run-123"
    assert params[1] == "SWPC"
    assert params[2] == "SUCCESS"
    assert params[5] == 57  # rows
    assert json.loads(params[7]) == {"batch_id": "abc"}


def test_log_unit_rejects_invalid_status(fake_db):
    logger = rl.StageRunLogger("ingestion", "run-123")
    with pytest.raises(AssertionError):
        logger.log_unit("SWPC", status="WEIRD")


def test_log_unit_rejects_header_only_stage(fake_db):
    logger = rl.StageRunLogger("batch", "run-123")
    with pytest.raises(AssertionError):
        logger.log_unit("x", status="SUCCESS")


def test_finish_aggregates_from_detail_table(fake_db):
    logger = rl.StageRunLogger("ingestion", "run-123")
    logger.finish(status="SUCCESS")

    # First executed statement (in finish) is the aggregate SELECT.
    select_sql, select_params = fake_db.executed[-2]
    assert "SELECT count(*), COALESCE(sum(rows), 0)" in select_sql
    assert select_params == ("run-123",)

    update_sql, update_params = fake_db.executed[-1]
    assert update_sql.startswith("UPDATE metadata.ingestion_run SET")
    assert "total_units = %s" in update_sql
    assert "total_rows = %s" in update_sql
    assert update_params[-1] == "run-123"


def test_finish_header_only_stage_skips_aggregate(fake_db):
    logger = rl.StageRunLogger("master", "run-1")
    logger.finish(status="SUCCESS", extra_columns={"batch_run_id": "batch-1"})

    update_sql, update_params = fake_db.executed[-1]
    assert update_sql.startswith("UPDATE metadata.master_run SET")
    assert "batch_run_id = %s" in update_sql
    assert "batch-1" in update_params


def test_finish_rejects_invalid_status(fake_db):
    logger = rl.StageRunLogger("ingestion", "run-123")
    with pytest.raises(AssertionError):
        logger.finish(status="NOPE")


def test_timed_logs_success_with_rows(fake_db):
    logger = rl.StageRunLogger("ingestion", "run-123")
    with rl.timed(logger, "SWPC") as result:
        result["rows"] = 57
        result["batch_id"] = "abc"

    sql, params = fake_db.executed[-1]
    assert "INSERT INTO metadata.ingestion_run_detail" in sql
    assert params[2] == "SUCCESS"
    assert params[5] == 57
    assert json.loads(params[7]) == {"batch_id": "abc"}


def test_timed_logs_failure_and_reraises(fake_db):
    logger = rl.StageRunLogger("ingestion", "run-123")
    with pytest.raises(RuntimeError):
        with rl.timed(logger, "SWPC"):
            raise RuntimeError("boom")

    sql, params = fake_db.executed[-1]
    assert "INSERT INTO metadata.ingestion_run_detail" in sql
    assert params[2] == "FAILED"
    assert params[6] == "boom"  # error_message


def test_run_logged_returns_callable_result(fake_db):
    logger = rl.StageRunLogger("ingestion", "run-123")

    def _fn():
        return {"records": 24, "batch_id": "xyz"}

    out = rl.run_logged(logger, "GFW", _fn, rows_key="records")

    assert out == {"records": 24, "batch_id": "xyz"}
    sql, params = fake_db.executed[-1]
    assert params[2] == "SUCCESS"
    assert params[5] == 24
