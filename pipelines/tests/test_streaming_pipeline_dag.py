from __future__ import annotations

import importlib
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


def test_streaming_ingestion_consumes_one_complete_produced_wave(monkeypatch):
    dag = importlib.import_module("pipelines.dags.streaming_pipeline_dag")
    produce = Mock(return_value=dag._WAVE_1_RECORDS)
    consume = Mock(return_value=dag._WAVE_1_RECORDS)
    validate = Mock(return_value={"valid": dag._WAVE_1_RECORDS, "invalid": 0})
    logger = Mock()

    monkeypatch.setitem(
        sys.modules,
        "ingestion.streaming.producers.telemetry_producer",
        SimpleNamespace(run=produce),
    )
    monkeypatch.setitem(
        sys.modules,
        "ingestion.streaming.consumers.raw_ingest_consumer",
        SimpleNamespace(run=consume),
    )
    monkeypatch.setitem(
        sys.modules,
        "ingestion.streaming.consumers.validation_consumer",
        SimpleNamespace(run=validate),
    )
    monkeypatch.setattr(dag, "_logger", lambda _context: logger)

    dag._produce_and_consume()

    consume.assert_called_once_with(batch_size=dag._WAVE_1_RECORDS, max_batches=1)
    validate.assert_called_once_with(max_records=dag._WAVE_1_RECORDS)
    produce.assert_called_once_with(dag._WAVE_1_RECORDS, rate_per_s=200.0, failure_rate=1.0)


def _patch_wave_2(monkeypatch, dag, rows):
    logger = Mock()
    monkeypatch.setattr(dag, "_logger", lambda _context: logger)
    monkeypatch.setattr(dag.time, "sleep", Mock())
    monkeypatch.setattr(subprocess, "run", Mock())
    produce = Mock(return_value=dag._WAVE_2_RECORDS)
    monkeypatch.setitem(
        sys.modules, "ingestion.streaming.producers.telemetry_producer", SimpleNamespace(run=produce),
    )
    monkeypatch.setitem(
        sys.modules,
        "ingestion.streaming.consumers.validation_consumer",
        SimpleNamespace(run=Mock(return_value={"valid": dag._WAVE_2_RECORDS, "invalid": 0})),
    )
    from pipelines.common import lake_metrics

    monkeypatch.setattr(lake_metrics, "count_parquet_rows", lambda _path: rows)
    return logger, produce, lake_metrics


def test_streaming_transform_fails_when_injected_anomalies_are_lost(monkeypatch):
    dag = importlib.import_module("pipelines.dags.streaming_pipeline_dag")
    logger, produce, lake_metrics = _patch_wave_2(monkeypatch, dag, rows=6)
    monkeypatch.setattr(lake_metrics, "stream_window_anomaly_summary", lambda _path: {
        "windows": 6, "samples": 150, "anomaly_samples": 0, "mixed_windows": 0,
    })

    with pytest.raises(RuntimeError, match="0 anomaly contributions; expected at least 60"):
        dag._advance_watermark_and_stop()

    produce.assert_called_once_with(dag._WAVE_2_RECORDS, rate_per_s=200.0, failure_rate=0.0)
    assert logger.log_unit.call_args.kwargs["status"] == "FAILED"
    logger.finish.assert_called_once()


def test_streaming_transform_fails_on_mixed_anomaly_windows(monkeypatch):
    dag = importlib.import_module("pipelines.dags.streaming_pipeline_dag")
    logger, _produce, lake_metrics = _patch_wave_2(monkeypatch, dag, rows=6)
    monkeypatch.setattr(lake_metrics, "stream_window_anomaly_summary", lambda _path: {
        "windows": 6, "samples": 150, "anomaly_samples": 120, "mixed_windows": 1,
    })

    with pytest.raises(RuntimeError, match="1 Silver windows mix"):
        dag._advance_watermark_and_stop()


def test_streaming_transform_passes_when_injected_anomalies_reach_silver(monkeypatch):
    dag = importlib.import_module("pipelines.dags.streaming_pipeline_dag")
    logger, _produce, lake_metrics = _patch_wave_2(monkeypatch, dag, rows=6)
    monkeypatch.setattr(lake_metrics, "stream_window_anomaly_summary", lambda _path: {
        "windows": 6, "samples": 120, "anomaly_samples": 120, "mixed_windows": 0,
    })

    dag._advance_watermark_and_stop()

    assert logger.log_unit.call_args.args == ("stream_sat_health_1m",)
    assert logger.log_unit.call_args.kwargs["status"] == "SUCCESS"
    logger.finish.assert_not_called()


def test_streaming_watermark_wait_covers_window_and_flush_triggers():
    dag = importlib.import_module("pipelines.dags.streaming_pipeline_dag")

    assert dag._WAIT_AFTER_WAVE_1_SECONDS >= 210
    assert dag._WAIT_AFTER_WAVE_2_SECONDS >= 60


def test_streaming_transform_fails_when_no_window_rows_are_written(monkeypatch):
    dag = importlib.import_module("pipelines.dags.streaming_pipeline_dag")
    logger = Mock()
    monkeypatch.setattr(dag, "_logger", lambda _context: logger)
    monkeypatch.setattr(dag.time, "sleep", Mock())
    monkeypatch.setattr(subprocess, "run", Mock())
    monkeypatch.setitem(
        sys.modules,
        "ingestion.streaming.producers.telemetry_producer",
        SimpleNamespace(run=Mock(return_value=dag._WAVE_2_RECORDS)),
    )
    monkeypatch.setitem(
        sys.modules,
        "ingestion.streaming.consumers.validation_consumer",
        SimpleNamespace(run=Mock(return_value={"valid": dag._WAVE_2_RECORDS, "invalid": 0})),
    )

    from pipelines.common import lake_metrics

    monkeypatch.setattr(lake_metrics, "count_parquet_rows", lambda _path: 2)

    with pytest.raises(RuntimeError, match="produced 2 rows.*expected at least 3"):
        dag._advance_watermark_and_stop()

    logger.log_unit.assert_any_call(
        "stream_sat_health_1m",
        status="FAILED",
        rows=2,
        details={
            "path": dag._STREAM_OUTPUT_PATH,
            "minimum_rows": 3,
            "reason": (
                f"Streaming transform produced 2 rows at {dag._STREAM_OUTPUT_PATH}; "
                "expected at least 3 (one window per satellite)"
            ),
        },
    )
    logger.finish.assert_called_once_with(
        status="FAILED",
        error=(
            f"Streaming transform produced 2 rows at {dag._STREAM_OUTPUT_PATH}; "
            "expected at least 3 (one window per satellite)"
        ),
    )
