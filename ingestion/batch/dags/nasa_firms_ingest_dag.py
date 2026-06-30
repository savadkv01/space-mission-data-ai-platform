"""DAG: NASA FIRMS active-fire batch ingestion (Task 3).

Schedule: hourly (FIRMS NRT updates within ~3h). Incremental: each run pulls the
last `days=1` window for the configured AOI and lands it in Bronze.
"""

from __future__ import annotations

from datetime import datetime

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:  # allows import/lint without Airflow installed
    DAG = None  # type: ignore
    PythonOperator = None  # type: ignore

from ingestion.api.nasa_firms import FirmsConnector
from ingestion.batch.dags._defaults import DEFAULT_ARGS
from ingestion.batch.ingest_task import run_connector_to_bronze

# AOI bounding boxes (lon/lat) for MVP wildfire monitoring regions.
REGIONS = {"mena": "30,10,60,40", "med": "-10,30,40,46"}


def _ingest_region(region: str, area: str, **_) -> dict:
    return run_connector_to_bronze(FirmsConnector(), source="VIIRS_SNPP_NRT", area=area, days=1)


if DAG is not None:
    with DAG(
        dag_id="ingest_nasa_firms",
        description="NASA FIRMS / VIIRS active fire -> Bronze",
        default_args=DEFAULT_ARGS,
        start_date=datetime(2024, 1, 1),
        schedule="@hourly",
        catchup=False,
        tags=["ingestion", "api", "nasa", "fire"],
    ) as dag:
        for _region, _area in REGIONS.items():
            PythonOperator(
                task_id=f"firms_{_region}",
                python_callable=_ingest_region,
                op_kwargs={"region": _region, "area": _area},
            )
