"""Kafka producer/consumer factories.

Thin wrappers over ``kafka-python`` that centralise serialization and config.
``kafka-python`` is imported lazily so the rest of the package (simulation,
envelope, validators, tests) imports without the dependency installed.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Iterator

from ingestion.common.logging_setup import get_logger
from ingestion.config.settings import settings

log = get_logger(__name__)


def _json_serializer(value: Any) -> bytes:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    return json.dumps(value, default=str).encode("utf-8")


def _key_serializer(key: Any) -> bytes | None:
    if key is None:
        return None
    return str(key).encode("utf-8")


def create_producer(**overrides):
    """Return a configured ``KafkaProducer`` (idempotent, acks=all)."""
    from kafka import KafkaProducer  # lazy import

    config = dict(
        bootstrap_servers=settings.kafka.bootstrap_servers,
        client_id=settings.kafka.client_id,
        value_serializer=_json_serializer,
        key_serializer=_key_serializer,
        acks="all",
        enable_idempotence=True,
        retries=5,
        linger_ms=50,
        compression_type="gzip",
    )
    config.update(overrides)
    log.info("creating Kafka producer -> %s", config["bootstrap_servers"])
    return KafkaProducer(**config)


def create_consumer(topics: list[str], *, group_id: str, auto_offset_reset: str = "earliest",
                    enable_auto_commit: bool = False, **overrides):
    """Return a configured ``KafkaConsumer`` with manual offset control.

    Manual commit (``enable_auto_commit=False``) supports at-least-once delivery:
    we only commit after the record has been durably landed in Bronze.
    """
    from kafka import KafkaConsumer  # lazy import

    config = dict(
        bootstrap_servers=settings.kafka.bootstrap_servers,
        group_id=group_id,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        key_deserializer=lambda b: b.decode("utf-8") if b else None,
        auto_offset_reset=auto_offset_reset,
        enable_auto_commit=enable_auto_commit,
        max_poll_records=200,
    )
    config.update(overrides)
    log.info("creating Kafka consumer group=%s topics=%s", group_id, topics)
    consumer = KafkaConsumer(*topics, **config)
    return consumer


def consume_forever(consumer, handler: Callable[[Any], None]) -> Iterator[None]:
    """Drive a consumer loop, committing offsets after each successful handle."""
    for message in consumer:
        try:
            handler(message)
            consumer.commit()
        except Exception:  # noqa: BLE001 — keep the loop alive; handler routes to DLQ
            log.exception("handler failed for offset %s; not committing", getattr(message, "offset", "?"))
        yield
