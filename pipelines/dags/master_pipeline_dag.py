"""Airflow DAG: platform_master_pipeline — trigger every pipeline sequentially.

    platform_batch_pipeline (ingestion -> transformation -> serving -> bi)
        -> platform_streaming_pipeline (streaming ingest -> bounded streaming transform)

This is the single "run everything" entry point; ``platform_batch_pipeline``
and ``platform_streaming_pipeline`` remain independently triggerable for
partial runs. Logs a ``metadata.master_run`` header row referencing the two
child runs' own ``run_id``s (deterministic, via ``trigger_run_id``) so the
whole trigger chain can be queried from one row.

No schedule — manual trigger only.
"""

from __future__ import annotations

from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.operators.trigger_dagrun import TriggerDagRunOperator
    _AIRFLOW = True
except Exception:  # noqa: BLE001 - optional dependency
    DAG = None  # type: ignore
    PythonOperator = None  # type: ignore
    TriggerDagRunOperator = None  # type: ignore
    _AIRFLOW = False

from pipelines.common.run_logger import StageRunLogger

DEFAULT_ARGS = {
    "owner": "data-platform",
    "retries": 0,
    "retry_delay": timedelta(minutes=1),
    "depends_on_past": False,
}

BATCH_DAG_ID = "platform_batch_pipeline"
STREAMING_DAG_ID = "platform_streaming_pipeline"


def _master_start(**context) -> None:
    StageRunLogger("master", context["run_id"], triggered_by="airflow").start()


def _master_finish(**context) -> None:
    """Look up the two child runs' final status and roll them up."""
    from pipelines.common.db import get_connection

    run_id = context["run_id"]
    batch_run_id = f"{run_id}__batch"
    streaming_run_id = f"{run_id}__streaming"

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT status FROM metadata.batch_run WHERE run_id = %s", (batch_run_id,))
        batch_row = cur.fetchone()
        cur.execute("SELECT status FROM metadata.streaming_run WHERE run_id = %s", (streaming_run_id,))
        streaming_row = cur.fetchone()

    batch_status = batch_row[0] if batch_row else "UNKNOWN"
    streaming_status = streaming_row[0] if streaming_row else "UNKNOWN"
    overall = "SUCCESS" if batch_status == "SUCCESS" and streaming_status == "SUCCESS" else "FAILED"
    error = None if overall == "SUCCESS" else f"batch={batch_status}, streaming={streaming_status}"

    StageRunLogger("master", run_id).finish(
        status=overall,
        error=error,
        extra_columns={"batch_run_id": batch_run_id, "streaming_run_id": streaming_run_id},
    )


def build_dag() -> "DAG | None":
    if not _AIRFLOW:
        return None

    dag = DAG(
        dag_id="platform_master_pipeline",
        description="Run everything: batch track fully, then the streaming track (manual trigger)",
        default_args=DEFAULT_ARGS,
        schedule=None,
        start_date=datetime(2026, 1, 1),
        catchup=False,
        max_active_runs=1,
        tags=["pipeline", "master"],
    )

    with dag:
        start = PythonOperator(task_id="master_start", python_callable=_master_start)

        trigger_batch = TriggerDagRunOperator(
            task_id="trigger_batch_pipeline",
            trigger_dag_id=BATCH_DAG_ID,
            trigger_run_id="{{ run_id }}__batch",
            conf={"parent_run_id": "{{ run_id }}"},
            wait_for_completion=True,
            poke_interval=30,
            reset_dag_run=True,
            failed_states=["failed"],
        )

        trigger_streaming = TriggerDagRunOperator(
            task_id="trigger_streaming_pipeline",
            trigger_dag_id=STREAMING_DAG_ID,
            trigger_run_id="{{ run_id }}__streaming",
            conf={"parent_run_id": "{{ run_id }}"},
            wait_for_completion=True,
            poke_interval=30,
            reset_dag_run=True,
            failed_states=["failed"],
        )

        finish = PythonOperator(
            task_id="master_finish",
            python_callable=_master_finish,
            trigger_rule="all_done",  # roll up + log status even if a child pipeline failed
        )

        start >> trigger_batch >> trigger_streaming >> finish

    return dag


dag = build_dag()
