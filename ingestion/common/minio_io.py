"""MinIO / S3 landing-zone writer.

Implements the Task 7 landing-zone layout. Bronze object keys follow:

    s3://bronze/<source>/ingest_date=YYYY-MM-DD/<batch_id>/<part>.jsonl

``boto3`` is imported lazily so non-storage code paths and unit tests do not
require the dependency.
"""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from typing import Iterable

from ingestion.common.envelope import BronzeEnvelope
from ingestion.common.logging_setup import get_logger
from ingestion.config.settings import settings

log = get_logger(__name__)


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def bronze_key(source: str, batch_id: str, part: str = "part-0000", *, ingest_date: str | None = None) -> str:
    """Build a partitioned Bronze object key (Hive-style ingest_date partition)."""
    ingest_date = ingest_date or _today()
    return f"{source}/ingest_date={ingest_date}/{batch_id}/{part}.jsonl"


class LandingZoneWriter:
    """Writes Bronze envelopes as newline-delimited JSON to MinIO."""

    def __init__(self, client=None, bucket: str | None = None) -> None:
        self._client = client
        self.bucket = bucket or settings.minio.bucket_bronze

    @property
    def client(self):
        if self._client is None:
            import boto3  # lazy import
            from botocore.config import Config

            self._client = boto3.client(
                "s3",
                endpoint_url=settings.minio.endpoint,
                aws_access_key_id=settings.minio.access_key,
                aws_secret_access_key=settings.minio.secret_key,
                region_name=settings.minio.region,
                config=Config(s3={"addressing_style": "path"}),
            )
        return self._client

    def write_batch(self, source: str, batch_id: str, envelopes: Iterable[BronzeEnvelope],
                    *, part: str = "part-0000") -> str:
        """Write a batch of envelopes to one Bronze object; returns the key."""
        buffer = io.StringIO()
        count = 0
        for env in envelopes:
            buffer.write(env.to_json())
            buffer.write("\n")
            count += 1
        key = bronze_key(source, batch_id, part)
        body = buffer.getvalue().encode("utf-8")
        self.client.put_object(Bucket=self.bucket, Key=key, Body=body,
                               ContentType="application/x-ndjson")
        log.info("wrote %d records -> s3://%s/%s (%d bytes)", count, self.bucket, key, len(body))
        return key

    def write_raw_object(self, key: str, body: bytes, content_type: str = "application/octet-stream",
                         *, bucket: str | None = None) -> str:
        """Land a raw file (CSV/JSON/binary) verbatim — used by file ingestion."""
        target = bucket or self.bucket
        self.client.put_object(Bucket=target, Key=key, Body=body, ContentType=content_type)
        log.info("wrote raw object -> s3://%s/%s (%d bytes)", target, key, len(body))
        return key
