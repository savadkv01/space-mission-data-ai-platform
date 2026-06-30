"""Lightweight local IO helpers for the offline demo and tests.

These read/write NDJSON and Parquet-like JSON snapshots on the local filesystem
so the transformation rules can be exercised end-to-end without an object store.
The Spark jobs use ``SparkSession.read/write`` against ``s3a://`` paths instead;
this module is intentionally dependency-light.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Iterator


def read_ndjson(path: str | Path) -> Iterator[dict[str, Any]]:
    """Yield one decoded record per non-empty line."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            yield json.loads(line)


def write_ndjson(path: str | Path, records: Iterable[dict[str, Any]]) -> int:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    lines = []
    for rec in records:
        lines.append(json.dumps(rec, default=str))
        count += 1
    p.write_text("\n".join(lines), encoding="utf-8")
    return count


def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")


def unwrap_bronze(envelope: dict[str, Any]) -> dict[str, Any]:
    """Extract the source ``payload`` from a Bronze envelope, preserving lineage.

    The returned record carries the original payload fields plus a small set of
    provenance columns (``_ingest_id``, ``_batch_id``, ``_source``, ``_event_ts``)
    so Silver remains fully traceable to its Bronze origin.
    """
    payload = envelope.get("payload", {})
    record = dict(payload) if isinstance(payload, dict) else {"value": payload}
    for prov in ("_ingest_id", "_batch_id", "_source", "_event_ts", "_ingest_ts"):
        if prov in envelope:
            record[prov] = envelope[prov]
    return record
