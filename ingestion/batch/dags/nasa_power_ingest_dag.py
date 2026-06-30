"""DAG: NASA POWER daily weather batch ingestion (Task 3).

Schedule: daily. Incremental: each run pulls the trailing 7-day window of daily
parameters for the configured AOI points and lands them in Bronze.
"""

from __future__ import annotations

from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:
    DAG = None  # type: ignore
    PythonOperator = None  # type: ignore

from ingestion.api.nasa_power import PowerConnector
from ingestion.batch.dags._defaults import DEFAULT_ARGS
from ingestion.batch.ingest_task import run_connector_to_bronze

# Monitoring points (lat, lon) aligned with MVP wildfire/flood AOIs.
POINTS = {"dubai": (25.20, 55.27), "lisbon": (38.72, -9.14)}


def _ingest(lat: float, lon: float, **context) -> dict:
    end = context.get("ds_nodash") or datetime.utcnow().strftime("%Y%m%d")
    start = (datetime.strptime(end, "%Y%m%d") - timedelta(days=7)).strftime("%Y%m%d")
    return run_connector_to_bronze(PowerConnector(), latitude=lat, longitude=lon, start=start, end=end)


if DAG is not None:
    with DAG(
        dag_id="ingest_nasa_power",
        description="NASA POWER daily weather -> Bronze",
        default_args=DEFAULT_ARGS,
        start_date=datetime(2024, 1, 1),
        schedule="@daily",
        catchup=False,
        tags=["ingestion", "api", "nasa", "weather"],
    ) as dag:
        for _name, (_lat, _lon) in POINTS.items():
            PythonOperator(
                task_id=f"power_{_name}",
                python_callable=_ingest,
                op_kwargs={"lat": _lat, "lon": _lon},
            )
