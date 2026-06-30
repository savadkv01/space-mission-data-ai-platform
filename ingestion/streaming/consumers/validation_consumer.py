"""Validation consumer: ``telemetry.satellite.raw`` -> ``cleaned`` or DLQ.

Reads raw telemetry, runs ingestion-time validation, and routes:
- valid records  -> ``telemetry.satellite.cleaned``
- invalid records -> quarantine + ``telemetry.satellite.dlq``

Implements the validation consumer (Task 2.5) and the error-handling / DLQ
strategy (Task 10).
"""

from __future__ import annotations

import argparse

from ingestion.common.envelope import build_envelope
from ingestion.common.kafka_io import create_consumer, create_producer
from ingestion.common.logging_setup import get_logger
from ingestion.config.settings import settings
from ingestion.quality.quarantine import Quarantine
from ingestion.quality.validators import DuplicateTracker, validate_record

log = get_logger("consumer.validation")

GROUP_ID = "telemetry-validator"


def run(max_records: int | None = None, producer=None) -> dict[str, int]:
    consumer = create_consumer([settings.kafka.topic_telemetry_raw], group_id=GROUP_ID)
    producer = producer or create_producer()
    quarantine = Quarantine(producer=producer, dlq_topic=settings.kafka.topic_telemetry_dlq)
    dedup = DuplicateTracker()
    stats = {"valid": 0, "invalid": 0}
    processed = 0
    try:
        for message in consumer:
            record = message.value
            env = build_envelope(source="TELEMETRY", payload=record, batch_id="validate",
                                 event_ts=record.get("timestamp"))
            outcome = validate_record(record, schema="satellite_telemetry",
                                      checksum=env._checksum, dedup=dedup)
            if outcome.valid:
                producer.send(settings.kafka.topic_telemetry_cleaned,
                              key=record.get("satellite_id"), value=record)
                stats["valid"] += 1
            else:
                quarantine.send("TELEMETRY", record, outcome.errors,
                                key=record.get("satellite_id"))
                stats["invalid"] += 1
            consumer.commit()
            processed += 1
            if max_records and processed >= max_records:
                break
    finally:
        producer.flush()
        consumer.close()
    log.info("validation done: %s", stats)
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate telemetry -> cleaned/DLQ")
    parser.add_argument("--max", type=int, default=None)
    args = parser.parse_args()
    run(args.max)
