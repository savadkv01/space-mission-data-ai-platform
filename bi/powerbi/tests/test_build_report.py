from __future__ import annotations

import csv
import importlib.util
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb
import pytest

MODULE = Path(__file__).resolve().parents[1] / "build_report.py"
SPEC = importlib.util.spec_from_file_location("powerbi_build", MODULE)
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


@pytest.mark.parametrize(("sql", "expected"), [
    ("SUM(detections)", "SUM('wildfire_daily'[detections])"),
    ("AVG(mean_frp)", "AVERAGE('wildfire_daily'[mean_frp])"),
    ("MAX(max_frp)", "MAX('wildfire_daily'[max_frp])"),
    ("COUNT(*)", "COALESCE(COUNTROWS('wildfire_daily'), 0)"),
    ("SUM(CASE WHEN dust_flag THEN 1 ELSE 0 END)",
     "SUMX('wildfire_daily', IF('wildfire_daily'[dust_flag] = TRUE(), 1, 0))"),
    ("AVG(CASE WHEN corroborated THEN 1.0 ELSE 0.0 END)",
     "AVERAGEX('wildfire_daily', IF('wildfire_daily'[corroborated] = TRUE(), 1.0, 0.0))"),
])
def test_supported_metric_translation(sql: str, expected: str) -> None:
    assert builder.metric_dax("wildfire_daily", sql) == expected


def test_numeric_case_guards_sql_null_semantics() -> None:
    expression = builder.metric_dax("weather", "SUM(CASE WHEN kp < 5 THEN 1 ELSE 0 END)")
    assert "NOT ISBLANK('weather'[kp]) &&" in expression


def test_unsupported_metrics_fail_explicitly() -> None:
    with pytest.raises(ValueError, match="Unsupported certified metric"):
        builder.metric_dax("table", "SUM(a) / SUM(b)")


def test_csv_null_boolean_unicode_and_dates(tmp_path: Path) -> None:
    path = tmp_path / "values.csv"
    builder.write_csv(path, ["text", "flag", "date", "number"], [
        ("AOI,\u00e9", True, date(2026, 10, 31), 42),
        ("", False, None, None),
    ])
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.reader(stream))
    assert rows[1] == ["AOI,\u00e9", "True", "2026-10-31", "42"]
    assert rows[2] == ["", "False", builder.NULL, builder.NULL]
    with pytest.raises(ValueError, match="Reserved CSV"):
        builder.write_csv(path, ["value"], [(builder.NULL,)])
    with pytest.raises(OverflowError, match="Int64"):
        builder.write_csv(path, ["value"], [(2**63,)])


def test_empty_dataset_is_reported_not_fabricated(tmp_path: Path) -> None:
    path = tmp_path / "test.duckdb"
    with duckdb.connect(str(path)) as connection:
        connection.execute("CREATE TABLE empty_source (event_date DATE, count BIGINT)")
    source = {"datasets": {"id": {
        "table_name": "empty", "sql": "select * from empty_source",
        "main_dttm_col": "event_date", "_file": "test.yaml",
    }}}
    columns, status = builder.extract(source, path, tmp_path / "data", tmp_path / ".env", "localhost:9000")
    assert columns["empty"] == [("event_date", "DATE"), ("count", "BIGINT")]
    assert status[0]["state"] == "EMPTY SOURCE"
    assert status[0]["rows"] == 0
    with (tmp_path / "data" / "empty.csv").open(encoding="utf-8") as stream:
        assert list(csv.reader(stream)) == [["event_date", "count"]]


def test_all_checked_in_metrics_and_chart_types_translate(tmp_path: Path) -> None:
    source = builder.assets()
    columns = {
        dataset["table_name"]: [(column["column_name"], column["type"]) for column in dataset["columns"]]
        for dataset in source["datasets"].values()
    }
    columns["ReportDate"] = [("Date", "DATE"), ("Month", "VARCHAR"), ("Day", "INTEGER")]
    model, measures = builder.make_model(source, columns, tmp_path / "data")
    assert len(model["model"]["tables"]) == 16
    names = [measure["name"] for table in model["model"]["tables"] for measure in table.get("measures", [])]
    assert len(names) == len(set(names)), "Desktop requires model-wide unique measure names"
    coverage = builder.make_report(source, measures, tmp_path)
    assert {item["chart_uuid"] for item in coverage} == set(source["charts"])
    assert len({item["dashboard"] for item in coverage}) == 7
    assert len({item["page"] for item in coverage}) == 15
    assert sum(bool(item["deviation"]) for item in coverage) == 2


def test_source_where_filters_are_preserved() -> None:
    source = builder.assets()
    chart = next(chart for chart in source["charts"].values() if "flood_extent_details" in chart["_file"])
    dataset = source["datasets"][chart["dataset_uuid"]]
    result, _ = builder.chart_visual(chart, dataset, {}, "test", 0, 0, 600, 300, 0)
    condition = result["filterConfig"]["filters"][0]["filter"]["Where"][0]["Condition"]
    assert condition["Comparison"]["Left"]["Column"]["Property"] == "flood_flag"
    assert condition["Comparison"]["Right"]["Literal"]["Value"] == "true"


def test_default_windows_are_explicit_utc_bounds() -> None:
    value = builder.window_filter(30, datetime(2026, 11, 1, tzinfo=timezone.utc))
    condition = value["filter"]["Where"][0]["Condition"]["And"]
    assert condition["Left"]["Comparison"]["Right"]["Literal"]["Value"] == "datetime'2026-10-03T00:00:00'"
    assert condition["Right"]["Comparison"]["Right"]["Literal"]["Value"] == "datetime'2026-11-02T00:00:00'"


def test_failed_export_does_not_replace_previous_snapshots(tmp_path: Path) -> None:
    output = tmp_path / "report"
    output.mkdir()
    marker = output / "data"
    marker.mkdir()
    (marker / "original.csv").write_text("unchanged", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        builder.build(tmp_path / "missing.duckdb", output, tmp_path / ".env", "localhost:9000")
    assert (marker / "original.csv").read_text(encoding="utf-8") == "unchanged"
    assert not list(output.glob("powerbi-export-*"))
