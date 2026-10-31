"""Run WP0 inventory and WP1/WP6 fire evidence against live MinIO and serving."""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from ingestion.common.minio_io import LandingZoneWriter
from transformation.batch.gold_lakehouse import load_aoi_reference
from transformation.common.io import write_json
from transformation.readiness import (
    DatasetProfile, catalog_entries, fire_readiness, source_inventory,
)

ROOT = Path(__file__).resolve().parents[2]
KEEP = {"bronze/FIRMS", "silver/silver_fire", "gold/fire_aoi_attribution",
        "gold/kpi_wildfire_aoi_daily", "gold/kpi_eo_daily"}


def json_records(text: str) -> Iterator[dict[str, Any]]:
    """Support JSON arrays/objects and the existing NDJSON fixtures named .json."""
    decoder = json.JSONDecoder()
    position = 0
    while position < len(text):
        if text[position].isspace():
            position += 1
            continue
        data, position = decoder.raw_decode(text, position)
        for row in data if isinstance(data, list) else [data]:
            if not isinstance(row, dict):
                raise ValueError("Snapshot input contains a non-object JSON record")
            yield row


def object_rows(client: Any, bucket: str, key: str, size: int) -> Iterator[dict[str, Any]]:
    if size > 64 * 1024 * 1024:
        raise ValueError(f"Object exceeds 64 MiB snapshot budget: s3://{bucket}/{key}")
    body = client.get_object(Bucket=bucket, Key=key)["Body"]
    try:
        if key.endswith((".jsonl", ".ndjson")):
            for line in body.iter_lines():
                if line:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError(f"Non-object JSONL record: s3://{bucket}/{key}")
                    yield row
        elif key.endswith(".json"):
            yield from json_records(body.read().decode("utf-8"))
        elif key.endswith(".parquet"):
            import duckdb
            with tempfile.TemporaryDirectory(prefix="readiness-") as directory:
                path = Path(directory) / "part.parquet"
                with path.open("wb") as target:
                    for chunk in body.iter_chunks(chunk_size=1024 * 1024):
                        target.write(chunk)
                with duckdb.connect() as connection:
                    relation = connection.read_parquet(str(path))
                    names = relation.columns
                    cursor = relation.execute()
                    while batch := cursor.fetchmany(1000):
                        for values in batch:
                            yield dict(zip(names, values))
    finally:
        body.close()


def serving_evidence(path: Path, now: datetime) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    import duckdb
    if not path.is_file():
        raise FileNotFoundError(f"Serving database is required: {path}")
    summaries = []
    wildfire = None
    with duckdb.connect(str(path), read_only=True) as connection:
        catalog = connection.execute("SELECT current_database()").fetchone()[0]
        tables = connection.execute(
            "SELECT table_schema, table_name FROM information_schema.tables "
            "WHERE table_name LIKE 'serving_%' ORDER BY table_schema, table_name"
        ).fetchall()
        for schema, table in tables:
            qualified = ".".join('"' + part.replace('"', '""') + '"'
                                 for part in (catalog, schema, table))
            cursor = connection.execute(f"SELECT * FROM {qualified}")
            columns = [column[0] for column in cursor.description]
            profile = DatasetProfile(f"duckdb://{schema}/{table}")
            rows = []
            while batch := cursor.fetchmany(1000):
                for values in batch:
                    row = dict(zip(columns, values))
                    profile.add(row)
                    if schema == "serving" and table == "serving_wildfire_daily":
                        if len(rows) >= 100_000:
                            raise ValueError("Serving wildfire evidence exceeds 100,000 rows")
                        rows.append(row)
            summaries.append({"schema": schema, "table": table, **profile.report(now)})
            if schema == "serving" and table == "serving_wildfire_daily":
                wildfire = rows
    if wildfire is None:
        raise ValueError("Required serving_wildfire_daily table is missing")
    return summaries, wildfire


def snapshot(client: Any, catalog: Path, serving_path: Path,
             now: datetime) -> dict[str, Any]:
    profiles: dict[str, DatasetProfile] = {}
    datasets: dict[str, dict[str, Any]] = {}
    retained: dict[str, list[dict[str, Any]]] = {key: [] for key in KEEP}
    byte_count = 0
    for bucket in ("bronze", "silver", "gold"):
        for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                family = key.split("/")[0]
                logical = f"{bucket}/{family}"
                uri = f"s3://{logical}"
                profile = profiles.setdefault(uri, DatasetProfile(uri))
                info = datasets.setdefault(uri, {"object_count": 0, "bytes": 0,
                                                 "unsupported_objects": [], "last_modified": None})
                info["object_count"] += 1
                info["bytes"] += obj["Size"]
                modified = obj["LastModified"].isoformat()
                info["last_modified"] = max(info["last_modified"] or modified, modified)
                if not key.endswith((".json", ".jsonl", ".ndjson", ".parquet")):
                    if not key.endswith("_SUCCESS"):
                        info["unsupported_objects"].append(key)
                    continue
                byte_count += obj["Size"]
                if byte_count > 512 * 1024 * 1024:
                    raise ValueError("Snapshot exceeds the 512 MiB scanned-input budget")
                for row in object_rows(client, bucket, key, obj["Size"]):
                    profile.add(row)
                    if logical in KEEP:
                        if len(retained[logical]) >= 100_000:
                            raise ValueError(f"Retained evidence exceeds 100,000 rows: {uri}")
                        retained[logical].append(row)
                current = client.head_object(Bucket=bucket, Key=key)
                if current["ETag"] != obj["ETag"]:
                    raise RuntimeError(f"Object changed while scanning: s3://{bucket}/{key}; rerun")
    serving_tables, serving_rows = serving_evidence(serving_path, now)
    entries = catalog_entries(catalog.read_text(encoding="utf-8"))
    files = {str(path.relative_to(ROOT)).replace("\\", "/")
             for path in (ROOT / "ingestion").rglob("*.py")}
    gold = {key.split("/")[1]: rows for key, rows in retained.items() if key.startswith("gold/")}
    fire = fire_readiness(retained["bronze/FIRMS"], retained["silver/silver_fire"],
                          gold, load_aoi_reference(), now, serving_rows)
    sources = source_inventory(entries, profiles, files, now)
    return {
        "report_version": 1, "snapshot_started_at": now.isoformat(),
        "snapshot_completed_at": datetime.now(timezone.utc).isoformat(),
        "catalog_count": len(entries), "sources": sources,
        "datasets": [{**profile.report(now), **datasets[uri],
                      "record_count_status": "partial" if datasets[uri]["unsupported_objects"]
                      else "complete"}
                     for uri, profile in sorted(profiles.items())],
        "serving_tables": serving_tables,
        "unmapped_bronze_families": sorted(
            uri for uri in profiles if uri.startswith("s3://bronze/") and not any(
                uri in source["expected_paths"]
                for source in sources
            )),
        "fire_product": fire,
        "limitations": "No credentials, source URIs, station/vessel payloads or raw records are emitted. "
        "Recent landing is evidence of prior access, not a live upstream probe. "
        "Unsupported objects and unknown time ranges are explicit. Source mappings are non-additive.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "docs" / "source-data-analysis" /
                        "01-dataset-inventory.md")
    parser.add_argument("--serving-db", type=Path, default=ROOT / "serving" / "dbt" / "serving.duckdb")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = snapshot(LandingZoneWriter().client, args.catalog, args.serving_db,
                      datetime.now(timezone.utc))
    write_json(args.output, report)
    print(json.dumps({"output": str(args.output),
                      "technical_status": report["fire_product"]["technical_status"],
                      "analysis_ready": False}))
    return 0 if report["fire_product"]["technical_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
