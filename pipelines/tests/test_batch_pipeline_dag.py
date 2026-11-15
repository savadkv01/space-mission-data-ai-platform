from __future__ import annotations

import importlib
from unittest.mock import Mock


def test_empty_gold_marts_are_logged_as_unavailable_not_zero(monkeypatch):
    dag = importlib.import_module("pipelines.dags.batch_pipeline_dag")
    logger = Mock()
    monkeypatch.setattr(dag, "_stage_logger", lambda _stage, _context: logger)
    from pipelines.common import lake_metrics

    monkeypatch.setattr(lake_metrics, "count_parquet_rows",
                        lambda path: 0 if "kpi_launch_monthly" in path else 5)

    dag._log_gold_marts()

    details = {call.args[0]: call.kwargs["details"] for call in logger.log_unit.call_args_list}
    assert details["gold_kpi_launch_monthly"]["data_availability"] == "unavailable"
    assert "data_availability" not in details["gold_kpi_wildfire_aoi_daily"]
