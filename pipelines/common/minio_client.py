"""Thin boto3 S3 client factory for MinIO, used by the streaming pipeline to
clear stale sink objects. Mirrors ``ingestion/common/minio_io.py``'s lazy
``boto3`` import convention."""

from __future__ import annotations

from pipelines.config.settings import settings


def get_s3_client():
    import boto3  # lazy import
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=settings.minio.endpoint,
        aws_access_key_id=settings.minio.access_key,
        aws_secret_access_key=settings.minio.secret_key,
        config=Config(s3={"addressing_style": "path"}),
    )
