"""API-to-Kafka bridge producer.

Pulls from a polling API connector and republishes each record onto a Kafka
topic, turning a request/response source into a stream. Used for sources that
update frequently (e.g. NOAA SWPC space weather -> ``space.weather.events``).

Run:
    python -m ingestion.streaming.producers.api_bridge_producer --source swpc
"""

from __future__ import annotations

import argparse

from ingestion.api.celestrak import CelestrakConnector
from ingestion.api.noaa_swpc import SwpcConnector
from ingestion.common.kafka_io import create_producer
from ingestion.common.logging_setup import get_logger
from ingestion.config.settings import settings

log = get_logger("producer.api_bridge")

# source name -> (connector class, target topic, key field)
BRIDGES = {
    "swpc": (SwpcConnector, settings.kafka.topic_space_weather, "time_tag"),
    "celestrak": (CelestrakConnector, settings.kafka.topic_orbit_stream, "NORAD_CAT_ID"),
}


def run(source: str) -> int:
    if source not in BRIDGES:
        raise SystemExit(f"unknown source '{source}'; choose from {list(BRIDGES)}")
    connector_cls, topic, key_field = BRIDGES[source]
    connector = connector_cls()
    producer = create_producer()
    sent = 0
    try:
        for env in connector.ingest():
            record = env.payload
            producer.send(topic, key=record.get(key_field), value=record)
            sent += 1
    finally:
        producer.flush()
        producer.close()
    log.info("bridged %d records from %s -> %s", sent, source, topic)
    return sent


def main() -> None:
    parser = argparse.ArgumentParser(description="API -> Kafka bridge")
    parser.add_argument("--source", required=True, choices=list(BRIDGES))
    args = parser.parse_args()
    run(args.source)


if __name__ == "__main__":
    main()
