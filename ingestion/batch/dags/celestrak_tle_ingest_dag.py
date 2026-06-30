"""DAG: CelesTrak TLE/GP orbital catalog batch ingestion (Task 3).

Schedule: every 6 hours (TLEs refresh a few times daily). Lands GP element sets
in Bronze for downstream orbit propagation and revisit planning.
"""

from __future__ import annotations

from datetime import datetime

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:
    DAG = None  # type: ignore
    PythonOperator = None  # type: ignore

from ingestion.api.celestrak import CelestrakConnector
from ingestion.batch.dags._defaults import DEFAULT_ARGS
from ingestion.batch.ingest_task import run_connector_to_bronze

GROUPS = ["stations", "active", "weather"]


def _ingest(group: str, **_) -> dict:
    return run_connector_to_bronze(CelestrakConnector(), group=group)


if DAG is not None:
    with DAG(
        dag_id="ingest_celestrak_tle",
        description="CelesTrak GP/TLE -> Bronze",
        default_args=DEFAULT_ARGS,
        start_date=datetime(2024, 1, 1),
        schedule="0 */6 * * *",
        catchup=False,
        tags=["ingestion", "api", "celestrak", "orbital"],
    ) as dag:
        for _group in GROUPS:
            PythonOperator(
                task_id=f"tle_{_group}",
                python_callable=_ingest,
                op_kwargs={"group": _group},
            )
