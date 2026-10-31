"""Airflow DAG: platform_streaming_pipeline — manual, bounded streaming track.

    streaming ingestion (telemetry produce -> Bronze raw consumer -> validation
    consumer, all bounded/run-to-completion despite the "streaming" name)
        -> streaming transform (Spark Structured Streaming Kafka -> windowed
           Silver Parquet; bounded to a demo session since a real streaming
           query never terminates on its own)

Logs to ``metadata.streaming_run`` / ``metadata.streaming_run_detail`` (one
detail row per unit: telemetry_produce, raw_ingest_consumer,
validation_consumer, stream_sat_health_1m) via ``pipelines.common.run_logger``.

The Spark Structured Streaming job (``transformation/streaming/spark_streaming.py``,
``awaitTermination()``) cannot be a normal run-to-completion Airflow task, so
this DAG reproduces the manual "bounded demo run" recipe from OPERATIONS.md
section 12 step 7: start the query detached, produce two waves of REAL
telemetry a little apart in wall-clock time (so the watermark genuinely
advances — no synthetic/hand-crafted NDJSON needed, which also sidesteps the
PowerShell-encoding footgun documented in repo memory), wait a couple of
30s trigger intervals, then stop it and read back the windowed row count.

No schedule — manual trigger only.
"""

from __future__ import annotations

import os
import shlex
import time
from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.bash import BashOperator
    from airflow.operators.python import PythonOperator
    _AIRFLOW = True
except Exception:  # noqa: BLE001 - optional dependency
    DAG = None  # type: ignore
    BashOperator = None  # type: ignore
    PythonOperator = None  # type: ignore
    _AIRFLOW = False

from pipelines.common import kafka_py312_shim  # noqa: F401 - side effect, see module docstring
from pipelines.common.run_logger import StageRunLogger

DEFAULT_ARGS = {
    "owner": "data-platform",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    "depends_on_past": False,
}

SPARK_CONTAINER = os.environ.get("SPARK_CONTAINER", "space-platform-spark-master-1")
_WORKDIR = "/opt/spark/work-dir"
_STREAM_SUBMIT = (
    "/opt/spark/bin/spark-submit"
    " --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.9,org.apache.hadoop:hadoop-aws:3.3.4"
    " --conf spark.jars.ivy=/tmp/.ivy2 --conf spark.sql.extensions="
    " --conf spark.driver.host=localhost --conf spark.driver.bindAddress=127.0.0.1"
)
_STREAM_OUTPUT_PATH = "s3://silver/stream_sat_health_1m/*.parquet"

# Keep the waves at least one window plus one watermark delay apart, then
# allow two trigger intervals for append-mode windows to flush.
_WAVE_1_RECORDS = 60
_WAVE_2_RECORDS = 30
_WAIT_AFTER_WAVE_1_SECONDS = 210
_WAIT_AFTER_WAVE_2_SECONDS = 60
_STREAM_READY_TIMEOUT_SECONDS = 120
_MIN_STREAM_OUTPUT_ROWS = 3


def _in_spark(cmd: str) -> str:
    return f"docker exec -u root -w {_WORKDIR} {SPARK_CONTAINER} bash -lc {shlex.quote(cmd)}"


def _parent_run_id(context) -> str | None:
    conf = context["dag_run"].conf or {}
    return conf.get("parent_run_id")


def _logger(context) -> StageRunLogger:
    return StageRunLogger(
        "streaming", context["run_id"], parent_run_id=_parent_run_id(context), triggered_by="airflow",
    )


def _streaming_start(**context) -> None:
    _logger(context).start()


def _ensure_topics(**_context) -> None:
    from ingestion.scripts.create_topics import create_topics

    create_topics()


def _produce_and_consume(**context) -> None:
    """Streaming ingestion: telemetry -> Bronze raw -> validated/cleaned.

    Bounded and idempotent (unique batch_id per Bronze write, at-least-once
    Kafka commits) — safe to re-trigger.
    """
    logger = _logger(context)

    from ingestion.streaming.producers.telemetry_producer import run as produce_telemetry

    start = time.monotonic()
    sent = produce_telemetry(_WAVE_1_RECORDS, rate_per_s=200.0)
    logger.log_unit("telemetry_produce", status="SUCCESS", rows=sent, duration_seconds=time.monotonic() - start)

    from ingestion.streaming.consumers.raw_ingest_consumer import run as consume_raw

    start = time.monotonic()
    written = consume_raw(batch_size=_WAVE_1_RECORDS, max_batches=1)
    logger.log_unit("raw_ingest_consumer", status="SUCCESS", rows=written, duration_seconds=time.monotonic() - start)

    from ingestion.streaming.consumers.validation_consumer import run as validate

    start = time.monotonic()
    outcome = validate(max_records=_WAVE_1_RECORDS)
    logger.log_unit(
        "validation_consumer",
        status="SUCCESS",
        rows=outcome.get("valid"),
        duration_seconds=time.monotonic() - start,
        details={"invalid": outcome.get("invalid")},
    )


def _clear_stale_sink(**_context) -> None:
    """Delete any prior sink output + ``_spark_metadata`` for this demo window
    (repo memory: a stale sink from an earlier run makes a fresh checkpoint
    silently commit zero new micro-batches — checkpoint/sink-metadata mismatch)."""
    from pipelines.common.minio_client import get_s3_client

    client = get_s3_client()
    resp = client.list_objects_v2(Bucket="silver", Prefix="stream_sat_health_1m/")
    for obj in resp.get("Contents", []):
        client.delete_object(Bucket="silver", Key=obj["Key"])


def _advance_watermark_and_stop(**context) -> None:
    """Produce + validate a second, later wave of real telemetry (advances the
    Structured Streaming watermark using genuine wall-clock event time — no
    synthetic NDJSON needed), wait for a couple of 30s trigger intervals, then
    stop the query and log the resulting windowed row count.

    The streaming transform reads ``telemetry.satellite.cleaned`` (not
    ``.raw``), so this wave must also go through validation — producing to
    raw alone never reaches the topic the Spark job actually consumes and the
    watermark (and the window) never advances.
    """
    import subprocess

    logger = _logger(context)

    time.sleep(_WAIT_AFTER_WAVE_1_SECONDS)

    from ingestion.streaming.producers.telemetry_producer import run as produce_telemetry
    from ingestion.streaming.consumers.validation_consumer import run as validate

    start = time.monotonic()
    sent = produce_telemetry(_WAVE_2_RECORDS, rate_per_s=200.0)
    outcome = validate(max_records=_WAVE_2_RECORDS)
    logger.log_unit(
        "telemetry_produce_wave_2",
        status="SUCCESS",
        rows=sent,
        duration_seconds=time.monotonic() - start,
        details={"validated": outcome.get("valid"), "invalid": outcome.get("invalid")},
    )

    time.sleep(_WAIT_AFTER_WAVE_2_SECONDS)

    subprocess.run(
        ["docker", "exec", "-u", "root", SPARK_CONTAINER, "pkill", "-f", "SparkSubmit"],
        check=False,
    )

    from pipelines.common.lake_metrics import count_parquet_rows

    rows = count_parquet_rows(_STREAM_OUTPUT_PATH)
    if rows < _MIN_STREAM_OUTPUT_ROWS:
        error = (
            f"Streaming transform produced {rows} rows at {_STREAM_OUTPUT_PATH}; "
            f"expected at least {_MIN_STREAM_OUTPUT_ROWS} (one window per satellite)"
        )
        logger.log_unit(
            "stream_sat_health_1m",
            status="FAILED",
            rows=rows,
            details={"path": _STREAM_OUTPUT_PATH, "minimum_rows": _MIN_STREAM_OUTPUT_ROWS, "reason": error},
        )
        logger.finish(status="FAILED", error=error)
        raise RuntimeError(error)

    logger.log_unit("stream_sat_health_1m", status="SUCCESS", rows=rows, details={"path": _STREAM_OUTPUT_PATH})


def _streaming_finish(**context) -> None:
    _logger(context).finish(status="SUCCESS")


def build_dag() -> "DAG | None":
    if not _AIRFLOW:
        return None

    dag = DAG(
        dag_id="platform_streaming_pipeline",
        description="Streaming track: telemetry produce/consume/validate -> bounded Spark windowed transform (manual trigger)",
        default_args=DEFAULT_ARGS,
        schedule=None,
        start_date=datetime(2026, 1, 1),
        catchup=False,
        max_active_runs=1,
        tags=["pipeline", "streaming"],
    )

    with dag:
        start = PythonOperator(task_id="streaming_start", python_callable=_streaming_start)
        ensure_topics = PythonOperator(task_id="ensure_topics", python_callable=_ensure_topics)
        ingest = PythonOperator(task_id="produce_and_consume", python_callable=_produce_and_consume)
        clear_sink = PythonOperator(task_id="clear_stale_sink", python_callable=_clear_stale_sink)
        clear_checkpoint = BashOperator(
            task_id="clear_checkpoint",
            bash_command=_in_spark("rm -rf /tmp/spark-checkpoints"),
        )
        start_stream = BashOperator(
            task_id="start_spark_streaming",
            bash_command=(
                f"docker exec -u root -d -w {_WORKDIR} {SPARK_CONTAINER} bash -lc "
                + shlex.quote(f"{_STREAM_SUBMIT} transformation/scripts/run_stream.py > /tmp/run_stream.log 2>&1")
                + f" && for _ in $(seq 1 {_STREAM_READY_TIMEOUT_SECONDS}); do "
                + f"if docker exec -u root {SPARK_CONTAINER} grep -q 'streaming query ready' /tmp/run_stream.log; then exit 0; fi; "
                + "sleep 1; "
                + "done; "
                + f"docker exec -u root {SPARK_CONTAINER} tail -n 80 /tmp/run_stream.log; "
                + "exit 1"
            ),
            retries=0,
        )
        advance_and_stop = PythonOperator(
            task_id="advance_watermark_and_stop", python_callable=_advance_watermark_and_stop, retries=0,
        )
        finish = PythonOperator(task_id="streaming_finish", python_callable=_streaming_finish)

        (
            start >> ensure_topics >> clear_sink >> clear_checkpoint >> start_stream
            >> ingest >> advance_and_stop >> finish
        )

    return dag


dag = build_dag()
