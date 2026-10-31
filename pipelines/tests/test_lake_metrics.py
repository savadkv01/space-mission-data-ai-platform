from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from pipelines.common import lake_metrics


class _FakeConnection:
    def __init__(self, *, fail_count: bool = False):
        self.statements: list[str] = []
        self.fail_count = fail_count
        self.closed = False
        self._result = None

    def execute(self, statement: str):
        normalized = " ".join(statement.split())
        self.statements.append(normalized)
        if normalized == "select current_database()":
            self._result = ("serving",)
        elif normalized.startswith("select count(*)"):
            if self.fail_count:
                raise RuntimeError("count query failed")
            self._result = (11,)
        else:
            self._result = None
        return self

    def fetchone(self):
        return self._result

    def close(self):
        self.closed = True


def _install_fake_duckdb(monkeypatch, connection: _FakeConnection):
    module = SimpleNamespace(connect=lambda *args, **kwargs: connection)
    monkeypatch.setitem(sys.modules, "duckdb", module)


def test_count_duckdb_table_rows_qualifies_catalog_schema_and_table(monkeypatch):
    connection = _FakeConnection()
    _install_fake_duckdb(monkeypatch, connection)

    rows = lake_metrics.count_duckdb_table_rows(
        "serving.duckdb", "serving.serving_wildfire_daily",
    )

    assert rows == 11
    assert (
        'select count(*) from "serving"."serving"."serving_wildfire_daily"'
        in connection.statements
    )
    assert "install httpfs; load httpfs;" in connection.statements
    assert connection.closed


def test_count_duckdb_table_rows_does_not_hide_query_errors(monkeypatch):
    connection = _FakeConnection(fail_count=True)
    _install_fake_duckdb(monkeypatch, connection)

    with pytest.raises(RuntimeError, match="count query failed"):
        lake_metrics.count_duckdb_table_rows(
            "serving.duckdb", "serving.serving_wildfire_daily",
        )

    assert connection.closed
