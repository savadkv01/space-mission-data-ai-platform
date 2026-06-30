"""Quarantine for bad data (Task 9 / Task 10).

Invalid records are never dropped. They are written to a quarantine area
(``s3://staging/quarantine/...``) and/or emitted to the Kafka DLQ, annotated
with the failing rules, so they can be inspected, fixed, and replayed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ingestion.common.envelope import BronzeEnvelope, build_envelope, new_batch_id
from ingestion.common.logging_setup import get_logger

log = get_logger(__name__)


def quarantine_key(source: str, batch_id: str) -> str:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"quarantine/{source}/ingest_date={day}/{batch_id}.jsonl"


class Quarantine:
    """Routes invalid records to a staging-bucket quarantine and/or Kafka DLQ."""

    def __init__(self, writer=None, producer=None, dlq_topic: str | None = None,
                 bucket: str = "staging") -> None:
        self.writer = writer
        self.producer = producer
        self.dlq_topic = dlq_topic
        self.bucket = bucket

    def _wrap(self, source: str, record: Any, errors: list[str], batch_id: str) -> BronzeEnvelope:
        env = build_envelope(source=source, payload=record, batch_id=batch_id, fmt="json")
        env_dict = env.to_dict()
        env_dict["_quarantine_reasons"] = errors
        # store reasons by mutating payload wrapper for the DLQ message
        return env

    def send(self, source: str, record: Any, errors: list[str], *, key: str | None = None) -> None:
        batch_id = new_batch_id(f"dlq-{source}")
        message = {"reasons": errors, "record": record, "_quarantined_at": datetime.now(timezone.utc).isoformat()}
        if self.producer and self.dlq_topic:
            self.producer.send(self.dlq_topic, key=key, value=message)
            log.warning("quarantined record -> DLQ %s reasons=%s", self.dlq_topic, errors)
        if self.writer:
            env = self._wrap(source, message, errors, batch_id)
            self.writer.write_batch(f"_quarantine/{source}", batch_id, [env])
