"""Create the Kafka topics defined in settings (idempotent).

Run (with infra up):
    python -m ingestion.scripts.create_topics
"""

from __future__ import annotations

from ingestion.common.logging_setup import get_logger
from ingestion.config.settings import settings

log = get_logger("scripts.create_topics")


def create_topics() -> None:
    from kafka.admin import KafkaAdminClient, NewTopic
    from kafka.errors import TopicAlreadyExistsError

    admin = KafkaAdminClient(bootstrap_servers=settings.kafka.bootstrap_servers,
                             client_id="topic-admin")
    new_topics = [
        NewTopic(name=name, num_partitions=parts,
                 replication_factor=settings.kafka.replication_factor)
        for name, parts in settings.kafka.all_topics.items()
    ]
    for topic in new_topics:
        try:
            admin.create_topics([topic])
            log.info("created topic %s (%d partitions)", topic.name, topic.num_partitions)
        except TopicAlreadyExistsError:
            log.info("topic already exists: %s", topic.name)
    admin.close()


if __name__ == "__main__":
    create_topics()
