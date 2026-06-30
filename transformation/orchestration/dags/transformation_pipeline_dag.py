"""Airflow DAG: medallion batch transformation pipeline (Task 6).

Dependency chain (see docs/transformation/06-batch-processing.md):

    bronze_to_silver_{telemetry,orbit,space_weather}
        -> gold_satellite_health
        -> gold_space_weather_impact
        -> feature_engineering
        -> dbt_run (gold marts)
        -> quality_checkpoint

Airflow is an optional dependency. The import is guarded so this file can be
parsed and unit-inspected without Airflow installed; when deployed it registers
a daily DAG using ``BashOperator`` calls into the transformation CLI.
"""

from __future__ import annotations

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

# Entity -> silver task command (incremental by execution date).
SILVER_ENTITIES = ["telemetry", "orbit", "space_weather"]


def build_dag() -> "DAG | None":
    if not _AIRFLOW:
        return None

    dag = DAG(
        dag_id="transformation_medallion_batch",
        description="Bronze->Silver->Gold daily transformation",
        schedule_interval="0 1 * * *",  # daily at 01:00 UTC
        start_date=datetime(2026, 1, 1),
        catchup=False,
        max_active_runs=1,
        default_args=DEFAULT_ARGS,
        tags=["transformation", "medallion", "phase9"],
    )

    with dag:
        silver_tasks = {
            entity: BashOperator(
                task_id=f"silver_{entity}",
                bash_command=f"python -m transformation.batch.bronze_to_silver --entity {entity} --date {{{{ ds }}}}",
            )
            for entity in SILVER_ENTITIES
        }

        gold_health = BashOperator(
            task_id="gold_satellite_health",
            bash_command="python -m transformation.batch.silver_to_gold --mart satellite_health --date {{ ds }}",
        )
        gold_weather = BashOperator(
            task_id="gold_space_weather_impact",
            bash_command="python -m transformation.batch.silver_to_gold --mart space_weather_impact --date {{ ds }}",
        )
        features = BashOperator(
            task_id="feature_engineering",
            bash_command="python -m transformation.features.feature_engineering --date {{ ds }}",
        )
        dbt_run = BashOperator(
            task_id="dbt_run_gold",
            bash_command="cd transformation/dbt && dbt run --select gold && dbt test --select gold",
        )
        checkpoint = BashOperator(
            task_id="quality_checkpoint",
            bash_command="python -m transformation.cleaning.validation_framework --date {{ ds }}",
        )

        silver_tasks["telemetry"] >> gold_health >> features
        [silver_tasks["telemetry"], silver_tasks["space_weather"]] >> gold_weather
        silver_tasks["orbit"] >> features
        features >> dbt_run >> checkpoint

    return dag


dag = build_dag()
