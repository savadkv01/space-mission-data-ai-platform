"""DAG: NASA POWER daily weather batch ingestion (Task 3).

Scheduled runs pull the trailing 7-day window. Manual runs may override the
window with ``dag_run.conf.start`` and ``dag_run.conf.end`` for backfills.
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
from ingestion.config.settings import settings
from ingestion.batch.ingest_task import run_connector_to_bronze

# NASA POWER is a point product; AOI centroids are representative context, not
# spatially averaged wind measurements.
POINTS = {
    aoi_id: ((bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2)
    for aoi_id, bbox in settings.climate.aois.items()
}


def _ingest(aoi_id: str, lat: float, lon: float, **context) -> dict:
    dag_run = context.get("dag_run")
    run_conf = getattr(dag_run, "conf", None) or {}
    end = _compact_date(
        run_conf.get("end") or context.get("ds_nodash") or datetime.utcnow().strftime("%Y%m%d")
    )
    start_value = run_conf.get("start")
    start = (
        _compact_date(start_value)
        if start_value
        else (datetime.strptime(end, "%Y%m%d") - timedelta(days=7)).strftime("%Y%m%d")
    )
    if start > end:
        raise ValueError(f"NASA POWER start date {start} is after end date {end}")
    return run_connector_to_bronze(
        PowerConnector(), latitude=lat, longitude=lon, aoi_id=aoi_id, start=start, end=end
    )


def _compact_date(value: str) -> str:
    return datetime.strptime(value.replace("-", ""), "%Y%m%d").strftime("%Y%m%d")


if DAG is not None:
    with DAG(
        dag_id="ingest_nasa_power",
        description="NASA POWER daily weather -> Bronze",
        default_args=DEFAULT_ARGS,
        start_date=datetime(2024, 1, 1),
        schedule="@daily",
        catchup=False,
        is_paused_upon_creation=False,
        tags=["ingestion", "api", "nasa", "weather"],
    ) as dag:
        for _aoi_id, (_lat, _lon) in POINTS.items():
            PythonOperator(
                task_id=f"power_{_aoi_id.lower().replace('-', '_')}",
                python_callable=_ingest,
                op_kwargs={"aoi_id": _aoi_id, "lat": _lat, "lon": _lon},
            )
