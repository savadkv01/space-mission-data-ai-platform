"""DAG: TROPOMI (Sentinel-5P) trace-gas batch ingestion (Phase 8b).

Schedule: daily. Each run requests the trailing 1-day per-AOI statistics for each
configured trace-gas / aerosol product from Google Earth Engine (free
Sentinel-5P L3 collections) and lands one Bronze record per (AOI, product,
bucket) (source ``TROPOMI``).
"""

from __future__ import annotations

from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:
    DAG = None  # type: ignore
    PythonOperator = None  # type: ignore

from ingestion.api.gee_s5p import GeeS5pConnector
from ingestion.batch.dags._defaults import DEFAULT_ARGS
from ingestion.batch.ingest_task import run_connector_to_bronze
from ingestion.config.settings import settings

# Urban UAE-GULF AOIs for air-quality monitoring (region source plan, ADR-12).
AOIS = list(settings.climate.region_sources["UAE-GULF"]["tropomi"])


def _ingest(aoi_id: str, product: str, **context) -> dict:
    end = context.get("ds") or datetime.utcnow().strftime("%Y-%m-%d")
    start = (datetime.strptime(end, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    datetime_range = f"{start}T00:00:00Z/{end}T23:59:59Z"
    return run_connector_to_bronze(
        GeeS5pConnector(), aoi_id=aoi_id, product=product, datetime_range=datetime_range
    )


if DAG is not None:
    with DAG(
        dag_id="ingest_tropomi",
        description="TROPOMI (Sentinel-5P) trace gases -> Bronze",
        default_args=DEFAULT_ARGS,
        start_date=datetime(2024, 1, 1),
        schedule="@daily",
        catchup=False,
        is_paused_upon_creation=False,
        tags=["ingestion", "api", "climate", "air-quality", "earth-engine"],
    ) as dag:
        for _aoi in AOIS:
            for _product in settings.climate.tropomi_products:
                PythonOperator(
                    task_id=f"tropomi_{_aoi.lower().replace('-', '_')}_{_product.lower()}",
                    python_callable=_ingest,
                    op_kwargs={"aoi_id": _aoi, "product": _product},
                )
