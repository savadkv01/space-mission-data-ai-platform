"""Scheduled, incremental Feast materialization through the feature-store gate."""

from __future__ import annotations

import json
import os
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:
    DAG = None
    PythonOperator = None


def _materialize_features() -> dict:
    endpoint = os.environ.get(
        "FEATURE_STORE_INTERNAL_URL", "http://feature-store:6566"
    ).rstrip("/")
    token = os.environ.get("FEATURE_STORE_JOB_TOKEN", "")
    if not token:
        raise RuntimeError(
            "FEATURE_STORE_JOB_TOKEN is required before scheduled materialization can run."
        )

    request = Request(
        f"{endpoint}/internal/materialize",
        data=json.dumps({"incremental": True}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Feature-Job-Token": token,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=300) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"Feature materialization returned HTTP {response.status}."
                )
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Feature materialization failed with HTTP {error.code}: {detail}"
        ) from error
    except URLError as error:
        raise RuntimeError(f"Feature store is unreachable: {error.reason}") from error


if DAG is not None:
    with DAG(
        dag_id="feature_store_materialization",
        description="Refresh readiness-approved Feast views and hourly air-quality features.",
        schedule="0 * * * *",
        start_date=datetime(2026, 1, 1),
        catchup=False,
        max_active_runs=1,
        tags=["features", "feast", "readiness-gated"],
    ) as dag:
        PythonOperator(
            task_id="incremental_materialization",
            python_callable=_materialize_features,
            execution_timeout=None,
        )
