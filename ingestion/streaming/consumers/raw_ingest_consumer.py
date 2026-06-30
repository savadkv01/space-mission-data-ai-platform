"""Raw ingestion consumer: ``telemetry.satellite.raw`` -> Bronze (MinIO).

This is the storage-writer consumer (Task 2.5). It batches messages and writes
them to the Bronze landing zone as newline-delimited JSON, committing Kafka
offsets only after a durable write (at-least-once delivery).
"""

from __future__ import annotations

import argparse

from ingestion.common.envelope import build_envelope, new_batch_id
from ingestion.common.kafka_io import create_consumer
from ingestion.common.logging_setup import get_logger
from ingestion.common.minio_io import LandingZoneWriter
from ingestion.config.settings import settings

log = get_logger("consumer.raw_ingest")

GROUP_ID = "bronze-raw-writer"


def run(batch_size: int = 200, max_batches: int | None = None, writer: LandingZoneWriter | None = None) -> int:
    consumer = create_consumer([settings.kafka.topic_telemetry_raw], group_id=GROUP_ID)
    writer = writer or LandingZoneWriter(bucket=settings.minio.bucket_bronze)
    buffer = []
    batches = 0
    total = 0
    try:
        for message in consumer:
            buffer.append(message.value)
            if len(buffer) >= batch_size:
                total += _flush(writer, buffer)
                consumer.commit()
                buffer.clear()
                batches += 1
                if max_batches and batches >= max_batches:
                    break
        if buffer:
            total += _flush(writer, buffer)
            consumer.commit()
    finally:
        consumer.close()
    log.info("raw consumer wrote %d records in %d batches", total, batches)
    return total


def _flush(writer: LandingZoneWriter, records: list[dict]) -> int:
    batch_id = new_batch_id("telemetry")
    envelopes = [
        build_envelope(source="TELEMETRY", payload=r, batch_id=batch_id,
                       fmt="json", event_ts=r.get("timestamp"))
        for r in records
    ]
    writer.write_batch("telemetry", batch_id, envelopes)
    return len(envelopes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kafka raw telemetry -> Bronze")
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--max-batches", type=int, default=None)
    args = parser.parse_args()
    run(args.batch_size, args.max_batches)
