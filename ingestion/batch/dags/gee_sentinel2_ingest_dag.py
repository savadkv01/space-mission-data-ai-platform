"""DAG: recent Sentinel-2 scene metadata and daily index statistics via GEE."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:
    DAG = None  # type: ignore
    PythonOperator = None  # type: ignore

from ingestion.api.gee_sentinel2 import (
    GeeSentinel2IndexConnector,
    GeeSentinel2SceneConnector,
)
from ingestion.batch.dags._defaults import DEFAULT_ARGS
from ingestion.batch.ingest_task import run_connector_to_bronze
from ingestion.config.settings import settings


def _recent_range() -> str:
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=14)
    end = today - timedelta(days=1)
    return f"{start.isoformat()}T00:00:00Z/{end.isoformat()}T23:59:59Z"


def _ingest_scenes(**_) -> dict:
    return run_connector_to_bronze(
        GeeSentinel2SceneConnector(),
        bbox=settings.climate.bbox("AOI-DXB"),
        datetime_range=_recent_range(),
        limit=20,
    )


def _ingest_index(index: str, **_) -> dict:
    return run_connector_to_bronze(
        GeeSentinel2IndexConnector(),
        index=index,
        bbox=settings.climate.bbox("AOI-DXB"),
        datetime_range=_recent_range(),
    )


if DAG is not None:
    with DAG(
        dag_id="ingest_gee_sentinel2",
        description="Sentinel-2 scene metadata and indices via Google Earth Engine",
        default_args=DEFAULT_ARGS,
        start_date=datetime(2024, 1, 1),
        schedule="@daily",
        catchup=False,
        is_paused_upon_creation=False,
        tags=["ingestion", "earth-observation", "sentinel-2", "earth-engine"],
    ) as dag:
        scenes = PythonOperator(
            task_id="sentinel2_scenes",
            python_callable=_ingest_scenes,
        )
        ndvi = PythonOperator(
            task_id="sentinel2_ndvi",
            python_callable=_ingest_index,
            op_kwargs={"index": "NDVI"},
        )
        ndwi = PythonOperator(
            task_id="sentinel2_ndwi",
            python_callable=_ingest_index,
            op_kwargs={"index": "NDWI"},
        )
        scenes >> ndvi >> ndwi
