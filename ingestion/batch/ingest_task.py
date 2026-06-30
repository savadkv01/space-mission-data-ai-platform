"""Shared batch ingestion task.

A single, connector-agnostic callable used by every batch DAG: it runs an API
connector, lands the resulting Bronze envelopes in MinIO, and returns the
object key. Keeping this here (not inside a DAG) makes it unit-testable without
Airflow installed.
"""

from __future__ import annotations

from typing import Any

from ingestion.api.base import ApiConnector
from ingestion.common.logging_setup import get_logger
from ingestion.common.minio_io import LandingZoneWriter

log = get_logger("batch.ingest_task")


def run_connector_to_bronze(connector: ApiConnector, *, writer: LandingZoneWriter | None = None,
                            **fetch_kwargs: Any) -> dict[str, Any]:
    """Pull from ``connector`` and land records in Bronze. Returns run metadata."""
    writer = writer or LandingZoneWriter()
    envelopes = connector.ingest(**fetch_kwargs)
    if not envelopes:
        log.warning("connector %s produced no records", connector.source_code)
        return {"source": connector.source_code, "records": 0, "key": None}
    batch_id = envelopes[0]._batch_id
    key = writer.write_batch(connector.source_code, batch_id, envelopes)
    return {"source": connector.source_code, "records": len(envelopes), "key": key, "batch_id": batch_id}
