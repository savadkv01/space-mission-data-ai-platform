"""Airflow DAG: medallion batch transformation pipeline (Task 6).

Dependency chain (see docs/transformation/06-batch-processing.md):

    silver_{telemetry,orbit,space_weather}   (Spark Bronze->Silver, S3A->MinIO)
        -> gold_dbt                          (dbt-duckdb Silver->Gold marts + tests)

The heavy engine (Spark + dbt) runs INSIDE the hardened ``spark-master``
container — which already carries the code mount, cached Ivy jars and the
MinIO/Kafka wiring — exactly as documented in OPERATIONS.md section 11. Airflow
does not run Spark locally; each task is dispatched with ``docker exec`` through
the mounted Docker socket, keeping the single heavy engine serialized on a
16 GB laptop. These are the same commands as ``scripts/run_pipeline.sh``.

Airflow is an optional dependency: the import is guarded so this file parses and
``build_dag()`` can be inspected without Airflow installed (see ``make dag-check``).
"""

from __future__ import annotations

import os
import shlex
from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.bash import BashOperator
    _AIRFLOW = True
except Exception:  # noqa: BLE001 - optional dependency
    DAG = None  # type: ignore
    BashOperator = None  # type: ignore
    _AIRFLOW = False

DEFAULT_ARGS = {
    "owner": "data-platform",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "depends_on_past": False,
}

# Entity -> Bronze->Silver Spark job.
SILVER_ENTITIES = ["telemetry", "orbit", "space_weather"]

# Hardened Spark/dbt runner (compose default container name; override via env).
SPARK_CONTAINER = os.environ.get("SPARK_CONTAINER", "space-platform-spark-master-1")
_WORKDIR = "/opt/spark/work-dir"
_SUBMIT = (
    "/opt/spark/bin/spark-submit"
    " --packages org.apache.hadoop:hadoop-aws:3.3.4"
    " --conf spark.jars.ivy=/tmp/.ivy2 --conf spark.sql.extensions="
    " --conf spark.driver.host=localhost --conf spark.driver.bindAddress=127.0.0.1"
)


def _in_spark(inner: str) -> str:
    """Wrap a shell command so it executes inside the spark-master container."""
    return f"docker exec -u root -w {_WORKDIR} {SPARK_CONTAINER} bash -lc {shlex.quote(inner)}"


def build_dag() -> "DAG | None":
    if not _AIRFLOW:
        return None

    dag = DAG(
        dag_id="transformation_medallion_batch",
        description="Bronze->Silver (Spark) -> Gold (dbt) daily transformation",
        schedule_interval="0 1 * * *",  # daily at 01:00 UTC
        start_date=datetime(2026, 1, 1),
        catchup=False,
        max_active_runs=1,
        default_args=DEFAULT_ARGS,
        tags=["transformation", "medallion", "phase9"],
    )

    with dag:
        silver_tasks = [
            BashOperator(
                task_id=f"silver_{entity}",
                bash_command=_in_spark(f"{_SUBMIT} transformation/scripts/run_silver.py {entity}"),
            )
            for entity in SILVER_ENTITIES
        ]

        gold_dbt = BashOperator(
            task_id="gold_dbt",
            bash_command=_in_spark("cd transformation/dbt && dbt deps && dbt run && dbt test"),
        )

        # All Silver jobs must succeed before the Gold marts are (re)built.
        silver_tasks >> gold_dbt

    return dag


dag = build_dag()
