"""File-based ingestion loader (Task 5).

Lands local CSV / JSON / Parquet files into the Bronze (or staging) zone in
MinIO, preserving the raw bytes and recording provenance. Trigger model:
- manual / CLI (this module)
- scheduled directory sweep (an Airflow DAG can call ``ingest_path``)

Folder convention in the landing zone:
    s3://bronze/<source>/ingest_date=YYYY-MM-DD/<batch_id>/<original_name>
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from ingestion.common.envelope import new_batch_id
from ingestion.common.logging_setup import get_logger
from ingestion.common.minio_io import LandingZoneWriter

log = get_logger("file.loader")

_CONTENT_TYPES = {
    ".csv": "text/csv",
    ".json": "application/json",
    ".jsonl": "application/x-ndjson",
    ".parquet": "application/vnd.apache.parquet",
}


def ingest_path(path: str | Path, *, source: str, writer: LandingZoneWriter | None = None,
                bucket: str = "bronze") -> list[str]:
    """Land a file or all files in a directory into the landing zone."""
    writer = writer or LandingZoneWriter(bucket=bucket)
    root = Path(path)
    files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    batch_id = new_batch_id(source)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    keys = []
    for file in files:
        key = f"{source}/ingest_date={day}/{batch_id}/{file.name}"
        content_type = _CONTENT_TYPES.get(file.suffix.lower(), "application/octet-stream")
        writer.write_raw_object(key, file.read_bytes(), content_type, bucket=bucket)
        keys.append(key)
    log.info("ingested %d file(s) from %s -> s3://%s", len(keys), root, bucket)
    return keys


def main() -> None:
    parser = argparse.ArgumentParser(description="Land local files into MinIO Bronze")
    parser.add_argument("path", help="file or directory to ingest")
    parser.add_argument("--source", required=True, help="dataset code, e.g. EMS, MISSION_LOGS")
    parser.add_argument("--bucket", default="bronze")
    args = parser.parse_args()
    ingest_path(args.path, source=args.source, bucket=args.bucket)


if __name__ == "__main__":
    main()
