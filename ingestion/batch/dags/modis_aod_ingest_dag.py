"""DAG: MODIS/VIIRS Aerosol Optical Depth batch ingestion (Phase 8b).

Schedule: daily. Each run requests trailing 1-day per-AOI AOD statistics for the
primary + dust-corridor AOIs from Google Earth Engine (free MODIS MAIAC AOD
collection) and lands one Bronze record per (AOI, day) (source ``MODIS_AOD``).
Dust-source corridors are included so plume transport toward the UAE can be
reconstructed downstream.
"""

from __future__ import annotations

from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:
    DAG = None  # type: ignore
    PythonOperator = None  # type: ignore

from ingestion.api.gee_aod import GeeAodConnector
from ingestion.batch.dags._defaults import DEFAULT_ARGS
from ingestion.batch.ingest_task import run_connector_to_bronze

# Primary UAE AOIs plus upwind dust-source corridors.
AOIS = ["AOI-UAE-NAT", "AOI-DESERT", "AOI-ARABIA", "AOI-IRAQ", "AOI-IRAN"]


def _ingest(aoi_id: str, **context) -> dict:
    end = context.get("ds") or datetime.utcnow().strftime("%Y-%m-%d")
    # MAIAC publication can lag several days; re-fetch a bounded window so late
    # imagery is picked up by later runs and downstream Silver dedupes by key.
    start = (datetime.strptime(end, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
    datetime_range = f"{start}T00:00:00Z/{end}T23:59:59Z"
    return run_connector_to_bronze(
        GeeAodConnector(), aoi_id=aoi_id, sensor="MODIS", datetime_range=datetime_range
    )


if DAG is not None:
    with DAG(
        dag_id="ingest_modis_aod",
        description="MODIS/VIIRS Aerosol Optical Depth -> Bronze",
        default_args=DEFAULT_ARGS,
        start_date=datetime(2024, 1, 1),
        schedule="@daily",
        catchup=False,
        is_paused_upon_creation=False,
        tags=["ingestion", "api", "climate", "dust", "earth-engine"],
    ) as dag:
        for _aoi in AOIS:
            PythonOperator(
                task_id=f"modis_aod_{_aoi.lower().replace('-', '_')}",
                python_callable=_ingest,
                op_kwargs={"aoi_id": _aoi},
            )
