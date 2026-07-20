"""Airflow DAG: platform_batch_pipeline — manual, full batch track.

    ingestion (batch APIs -> Bronze)
        -> transformation (Bronze -> Silver -> Gold, Spark + dbt demonstrator)
        -> serving (Gold -> dbt data products)
        -> bi (Superset dataset refresh)

Every stage logs a run-header row (``metadata.<stage>_run``) plus one detail
row per source/entity/model/dataset (``metadata.<stage>_run_detail``) via
``pipelines.common.run_logger``; see ``infrastructure/configs/postgres/init/
02-pipeline-run-logging.sql`` for the schema. ``run_id`` is this DAG run's own
Airflow ``run_id``, threaded through every stage so the whole trail can be
queried by one value; ``parent_run_id`` (passed via ``dag_run.conf`` when
triggered by ``platform_master_pipeline``) links it back to the master run.

No schedule — manual trigger only (``airflow dags trigger platform_batch_pipeline``
or the UI). Heavy engines (Spark/dbt) are dispatched via ``docker exec`` into
the already-hardened ``spark-master`` container, exactly like
``transformation/orchestration/dags/transformation_pipeline_dag.py`` and
``OPERATIONS.md`` section 12 — this DAG is the same recipe, orchestrated.
"""

from __future__ import annotations

import os
import shlex
from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.bash import BashOperator
    from airflow.operators.python import PythonOperator
    from airflow.utils.task_group import TaskGroup
    _AIRFLOW = True
except Exception:  # noqa: BLE001 - optional dependency, see make dag-check
    DAG = None  # type: ignore
    BashOperator = None  # type: ignore
    PythonOperator = None  # type: ignore
    TaskGroup = None  # type: ignore
    _AIRFLOW = False

from pipelines.common.run_logger import StageRunLogger

DEFAULT_ARGS = {
    "owner": "data-platform",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "depends_on_past": False,
}

SPARK_CONTAINER = os.environ.get("SPARK_CONTAINER", "space-platform-spark-master-1")
_WORKDIR = "/opt/spark/work-dir"
_SUBMIT = (
    "/opt/spark/bin/spark-submit"
    " --packages org.apache.hadoop:hadoop-aws:3.3.4"
    " --conf spark.jars.ivy=/tmp/.ivy2 --conf spark.sql.extensions="
    " --conf spark.driver.host=localhost --conf spark.driver.bindAddress=127.0.0.1"
)

SILVER_ENTITIES = ["telemetry", "orbit", "space_weather", "fire", "vessel", "scene", "index"]
CLIMATE_SILVER_ENTITIES = ["air_quality", "aerosol", "atmos_column"]

# Gold mart names (transformation/batch/gold_lakehouse.py build_marts() keys).
GOLD_MARTS = [
    "kpi_wildfire_aoi_daily", "kpi_flood_aoi_daily", "fact_vessel_activity",
    "fact_scene_catalog", "kpi_eo_daily", "kpi_aoi_validation", "ref_aoi",
    "fact_air_quality_daily", "fact_dust_event_daily",
    "fact_climate_indicator_daily", "fact_vegetation_health_daily",
    "fact_sat_health", "kpi_launch_monthly", "fact_weather_impact",
]

# Serving dbt model names (serving/dbt/models/**/*.sql) — matches the 14
# models built by `dbt run` (semantic views + serving tables + serving_agg
# materialized rollups). serving_sat_health/launch_monthly/weather_impact are
# NOT dbt models (those are the pure-Python serving/marts/serving_marts.py
# sim-track builders, ADR-SV-01) — not logged here.
SERVING_MODELS = [
    "serving_aoi_validation", "serving_scene_catalog", "serving_vessel_activity",
    "serving_air_quality_daily", "serving_climate_indicator_daily",
    "serving_dust_event_daily", "serving_flood_daily",
    "serving_vegetation_health_daily", "serving_wildfire_daily",
    "dim_aoi", "dim_climate_indicator", "dim_pollutant",
    "mv_kpi_climate_daily", "mv_kpi_platform_daily",
]


def _in_spark(inner: str, *, env: dict[str, str] | None = None) -> str:
    """Wrap a shell command so it executes inside the spark-master container."""
    env_flags = "".join(f" -e {k}={shlex.quote(v)}" for k, v in (env or {}).items())
    return f"docker exec -u root{env_flags} -w {_WORKDIR} {SPARK_CONTAINER} bash -lc {shlex.quote(inner)}"


def _parent_run_id(context) -> str | None:
    conf = context["dag_run"].conf or {}
    return conf.get("parent_run_id")


def _stage_logger(stage: str, context) -> StageRunLogger:
    return StageRunLogger(
        stage, context["run_id"], parent_run_id=_parent_run_id(context), triggered_by="airflow",
    )


# ---------------------------------------------------------------------------
# Ingestion stage — one task: reuses ingestion/scripts/run_full_batch_ingest.py
# (already the canonical "ingest everything now" driver, per-source try/except
# resilience already built in) and logs one detail row per source.
# ---------------------------------------------------------------------------
def _run_ingestion(**context) -> dict:
    logger = _stage_logger("ingestion", context)
    logger.start()
    try:
        from ingestion.scripts.run_full_batch_ingest import main as ingest_all
        results = ingest_all()
    except Exception as exc:  # noqa: BLE001
        logger.finish(status="FAILED", error=str(exc))
        raise

    for unit_name, result in results.items():
        if isinstance(result, dict) and "error" in result:
            logger.log_unit(unit_name, status="FAILED", error=str(result["error"]))
        else:
            logger.log_unit(
                unit_name,
                status="SUCCESS",
                rows=result.get("records"),
                details={"batch_id": result.get("batch_id"), "key": result.get("key")},
            )
    # Stage itself succeeds even if individual sources failed/produced 0 rows —
    # mirrors run_full_batch_ingest.py's existing tolerant, per-source design.
    logger.finish(status="SUCCESS")
    return {k: v.get("records") for k, v in results.items() if isinstance(v, dict)}


# ---------------------------------------------------------------------------
# Transformation stage — per-entity/mart row-count logging via DuckDB httpfs
# (no Spark needed in the Airflow container; see pipelines/common/lake_metrics.py).
# ---------------------------------------------------------------------------
def _transformation_start(**context) -> None:
    _stage_logger("transformation", context).start()


def _log_silver_entity(entity: str, **context) -> None:
    from pipelines.common.lake_metrics import count_parquet_rows

    logger = _stage_logger("transformation", context)
    rows = count_parquet_rows(f"s3://silver/silver_{entity}/*.parquet")
    logger.log_unit(f"silver_{entity}", status="SUCCESS", rows=rows, details={"layer": "silver"})


def _log_gold_marts(**context) -> None:
    from pipelines.common.lake_metrics import count_parquet_rows

    logger = _stage_logger("transformation", context)
    for mart in GOLD_MARTS:
        rows = count_parquet_rows(f"s3://gold/{mart}/*.parquet")
        logger.log_unit(f"gold_{mart}", status="SUCCESS", rows=rows, details={"layer": "gold"})


def _log_gold_dbt_demonstrator(**context) -> None:
    logger = _stage_logger("transformation", context)
    logger.log_unit("gold_dbt_demonstrator", status="SUCCESS", details={"layer": "gold_dbt"})


def _transformation_finish(**context) -> None:
    _stage_logger("transformation", context).finish(status="SUCCESS")


# ---------------------------------------------------------------------------
# Serving stage — dbt build (one-off spark-transform container, per
# OPERATIONS.md section 8/11-C), then per-model row counts from the
# bind-mounted serving.duckdb file (already on the Airflow repo mount).
# ---------------------------------------------------------------------------
_SERVING_DUCKDB_PATH = "/opt/airflow/repo/serving/dbt/serving.duckdb"

_SERVING_MODEL_SCHEMA = {
    "mv_kpi_climate_daily": "serving_agg",
    "mv_kpi_platform_daily": "serving_agg",
    "dim_aoi": "semantic",
    "dim_climate_indicator": "semantic",
    "dim_pollutant": "semantic",
}


def _serving_start(**context) -> None:
    _stage_logger("serving", context).start()


def _log_serving_models(**context) -> None:
    from pipelines.common.lake_metrics import count_duckdb_table_rows

    logger = _stage_logger("serving", context)
    for model in SERVING_MODELS:
        schema = _SERVING_MODEL_SCHEMA.get(model, "serving")
        rows = count_duckdb_table_rows(_SERVING_DUCKDB_PATH, f"{schema}.{model}")
        logger.log_unit(model, status="SUCCESS", rows=rows)


def _serving_finish(**context) -> None:
    _stage_logger("serving", context).finish(status="SUCCESS")


# ---------------------------------------------------------------------------
# BI stage — refresh every certified Superset dataset (column metadata reload).
# ---------------------------------------------------------------------------
def _run_bi_refresh(**context) -> None:
    from pipelines.common.superset_client import SupersetClient

    logger = _stage_logger("bi", context)
    logger.start()
    try:
        client = SupersetClient()
        datasets = client.list_datasets()
    except Exception as exc:  # noqa: BLE001
        logger.finish(status="FAILED", error=str(exc))
        raise

    for ds in datasets:
        name = ds.get("table_name", str(ds["id"]))
        try:
            client.refresh_dataset(ds["id"])
            logger.log_unit(name, status="SUCCESS", details={"dataset_id": ds["id"]})
        except Exception as exc:  # noqa: BLE001 - keep refreshing the rest
            logger.log_unit(name, status="FAILED", error=str(exc), details={"dataset_id": ds["id"]})
    logger.finish(status="SUCCESS")


# ---------------------------------------------------------------------------
# batch_run header (top-level rollup across all four stages).
# ---------------------------------------------------------------------------
def _batch_start(**context) -> None:
    run_id = context["run_id"]
    parent_run_id = _parent_run_id(context)
    StageRunLogger("batch", run_id, parent_run_id=parent_run_id, triggered_by="airflow").start()


def _batch_finish(**context) -> None:
    """Aggregate total_rows across the 4 stage headers into batch_run."""
    from pipelines.common.db import get_connection

    run_id = context["run_id"]
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(sum(total_rows), 0) FROM (
                SELECT total_rows FROM metadata.ingestion_run WHERE run_id = %s
                UNION ALL
                SELECT total_rows FROM metadata.transformation_run WHERE run_id = %s
                UNION ALL
                SELECT total_rows FROM metadata.serving_run WHERE run_id = %s
            ) t
            """,
            (run_id, run_id, run_id),
        )
        (total_rows,) = cur.fetchone()

    StageRunLogger("batch", run_id).finish(status="SUCCESS", extra_columns={"total_rows": int(total_rows)})


def build_dag() -> "DAG | None":
    if not _AIRFLOW:
        return None

    dag = DAG(
        dag_id="platform_batch_pipeline",
        description="Batch track: ingestion -> transformation -> serving -> bi (manual trigger)",
        default_args=DEFAULT_ARGS,
        schedule=None,
        start_date=datetime(2026, 1, 1),
        catchup=False,
        max_active_runs=1,
        tags=["pipeline", "batch"],
    )

    with dag:
        batch_start = PythonOperator(task_id="batch_start", python_callable=_batch_start)

        ingestion = PythonOperator(task_id="ingestion_batch_ingest", python_callable=_run_ingestion)

        with TaskGroup(group_id="transformation") as transformation:
            t_start = PythonOperator(task_id="start", python_callable=_transformation_start)

            silver_chains = []
            for entity in SILVER_ENTITIES:
                run_task = BashOperator(
                    task_id=f"silver_{entity}",
                    bash_command=_in_spark(f"{_SUBMIT} transformation/scripts/run_silver.py {entity}"),
                )
                log_task = PythonOperator(
                    task_id=f"log_silver_{entity}",
                    python_callable=_log_silver_entity,
                    op_kwargs={"entity": entity},
                )
                run_task >> log_task
                silver_chains.append((run_task, log_task))

            climate_chains = []
            for entity in CLIMATE_SILVER_ENTITIES:
                run_task = BashOperator(
                    task_id=f"silver_{entity}",
                    bash_command=_in_spark(f"{_SUBMIT} transformation/scripts/run_climate_silver.py {entity}"),
                )
                log_task = PythonOperator(
                    task_id=f"log_silver_{entity}",
                    python_callable=_log_silver_entity,
                    op_kwargs={"entity": entity},
                )
                run_task >> log_task
                climate_chains.append((run_task, log_task))

            gold_lakehouse = BashOperator(
                task_id="gold_lakehouse",
                bash_command=_in_spark(f"{_SUBMIT} transformation/scripts/run_gold.py"),
            )
            log_gold = PythonOperator(task_id="log_gold_marts", python_callable=_log_gold_marts)

            gold_dbt = BashOperator(
                task_id="gold_dbt_demonstrator",
                bash_command=_in_spark("cd transformation/dbt && dbt deps && dbt run && dbt test"),
            )
            log_gold_dbt = PythonOperator(task_id="log_gold_dbt", python_callable=_log_gold_dbt_demonstrator)

            t_finish = PythonOperator(task_id="finish", python_callable=_transformation_finish)

            # IMPORTANT: chain every Spark job STRICTLY sequentially. All of these
            # exec into the SAME spark-master container (2g mem_limit, local[*]);
            # running Silver entities concurrently (the naive "list of independent
            # tasks" pattern) starves that single JVM and OOMs it (verified live:
            # 10 concurrent spark-submits pinned the container at 99.99% of 2GiB).
            # This mirrors the documented constraint already followed by
            # transformation/scripts/run_pipeline.sh ("Run entities ONE at a time").
            all_chains = silver_chains + climate_chains
            previous = t_start
            for run_task, log_task in all_chains:
                previous >> run_task >> log_task
                previous = log_task
            previous >> gold_lakehouse >> log_gold >> gold_dbt >> log_gold_dbt >> t_finish

        with TaskGroup(group_id="serving") as serving:
            s_start = PythonOperator(task_id="start", python_callable=_serving_start)
            dbt_build = BashOperator(
                task_id="dbt_build",
                # Same container as the transformation stage (docker exec, no
                # separate one-off container / host-path bind mount needed) —
                # override DBT_PROFILES_DIR/SERVING_DUCKDB_PATH for this exec
                # only, since the container's own env is pinned to the
                # transformation Gold-dbt demonstrator project.
                bash_command=_in_spark(
                    "cd serving/dbt && dbt deps && dbt run && dbt test",
                    env={
                        "DBT_PROFILES_DIR": f"{_WORKDIR}/serving/dbt",
                        "SERVING_DUCKDB_PATH": f"{_WORKDIR}/serving/dbt/serving.duckdb",
                        "DUCKDB_S3_ENDPOINT": "minio:9000",
                    },
                ),
            )
            log_serving = PythonOperator(task_id="log_serving_models", python_callable=_log_serving_models)
            s_finish = PythonOperator(task_id="finish", python_callable=_serving_finish)
            s_start >> dbt_build >> log_serving >> s_finish

        bi = PythonOperator(task_id="bi_refresh", python_callable=_run_bi_refresh)

        batch_finish = PythonOperator(task_id="batch_finish", python_callable=_batch_finish)

        batch_start >> ingestion >> transformation >> serving >> bi >> batch_finish

    return dag


dag = build_dag()
