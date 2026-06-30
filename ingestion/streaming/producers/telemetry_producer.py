"""Synthetic telemetry producer: simulation -> Kafka ``telemetry.satellite.raw``.

Partitioning (Task 2): the message key is ``satellite_id`` so all telemetry for
a satellite lands on the same partition, preserving per-satellite ordering.

Run:
    python -m ingestion.streaming.producers.telemetry_producer --max 1000 --rate 50
"""

from __future__ import annotations

import argparse
import time

from ingestion.common.kafka_io import create_producer
from ingestion.common.logging_setup import get_logger
from ingestion.config.settings import settings
from ingestion.simulation.telemetry_generator import TelemetryGenerator

log = get_logger("producer.telemetry")


def run(max_records: int | None, rate_per_s: float, seed: int = 42) -> int:
    generator = TelemetryGenerator(seed=seed)
    producer = create_producer()
    topic = settings.kafka.topic_telemetry_raw
    interval = 1.0 / rate_per_s if rate_per_s > 0 else 0.0
    sent = 0
    try:
        for record in generator.stream(max_records=max_records):
            producer.send(topic, key=record["satellite_id"], value=record)
            sent += 1
            if sent % 100 == 0:
                log.info("produced %d telemetry records", sent)
            if interval:
                time.sleep(interval)
    finally:
        producer.flush()
        producer.close()
        log.info("done; produced %d records to %s", sent, topic)
    return sent


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic telemetry -> Kafka")
    parser.add_argument("--max", type=int, default=1000, help="records to produce (0 = infinite)")
    parser.add_argument("--rate", type=float, default=50.0, help="records/second")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(None if args.max == 0 else args.max, args.rate, args.seed)


if __name__ == "__main__":
    main()
