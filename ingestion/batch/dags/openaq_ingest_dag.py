"""DAG: OpenAQ ground-station air-quality batch ingestion (Phase 8b).

Schedule: daily. Each run pulls the trailing 1-day window of measurements for the
configured pollutants inside the urban AOIs and lands them in Bronze (source
``OPENAQ``).
"""

from __future__ import annotations

from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:
    DAG = None  # type: ignore
    PythonOperator = None  # type: ignore

from ingestion.api.openaq import OpenAqConnector
from ingestion.batch.dags._defaults import DEFAULT_ARGS
from ingestion.batch.ingest_task import run_connector_to_bronze

# Urban AOIs where ground stations exist (sparse over the Gulf).
AOIS = ["AOI-DXB", "AOI-AUH", "AOI-UAE-NAT"]


def _ingest(aoi_id: str, **context) -> dict:
    end = context.get("ds") or datetime.utcnow().strftime("%Y-%m-%d")
    start = (datetime.strptime(end, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    return run_connector_to_bronze(
        OpenAqConnector(), aoi_id=aoi_id, date_from=start, date_to=end
    )


if DAG is not None:
    with DAG(
        dag_id="ingest_openaq",
        description="OpenAQ ground air quality -> Bronze",
        default_args=DEFAULT_ARGS,
        start_date=datetime(2024, 1, 1),
        schedule="@daily",
        catchup=False,
        is_paused_upon_creation=False,
        tags=["ingestion", "api", "climate", "air-quality"],
    ) as dag:
        for _aoi in AOIS:
            PythonOperator(
                task_id=f"openaq_{_aoi.lower().replace('-', '_')}",
                python_callable=_ingest,
                op_kwargs={"aoi_id": _aoi},
            )
