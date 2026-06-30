"""DAG: NOAA SWPC space-weather batch ingestion (Task 3).

Schedule: every 15 minutes (near-real-time Kp product). Lands planetary K-index
records in Bronze. (A streaming variant exists via the API->Kafka bridge.)
"""

from __future__ import annotations

from datetime import datetime

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:
    DAG = None  # type: ignore
    PythonOperator = None  # type: ignore

from ingestion.api.noaa_swpc import SwpcConnector
from ingestion.batch.dags._defaults import DEFAULT_ARGS
from ingestion.batch.ingest_task import run_connector_to_bronze


def _ingest(**_) -> dict:
    return run_connector_to_bronze(SwpcConnector())


if DAG is not None:
    with DAG(
        dag_id="ingest_noaa_swpc",
        description="NOAA SWPC planetary K-index -> Bronze",
        default_args=DEFAULT_ARGS,
        start_date=datetime(2024, 1, 1),
        schedule="*/15 * * * *",
        catchup=False,
        tags=["ingestion", "api", "noaa", "space-weather"],
    ) as dag:
        PythonOperator(task_id="swpc_kp", python_callable=_ingest)
