"""Data lineage + run metadata (Task 13).

Every transformation run emits a :class:`LineageRecord` capturing inputs,
outputs, row counts, the code version, and a deterministic run id. These records
are written next to the output and are the basis for reproducibility and audit.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_run_id(job: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{job}-{stamp}-{uuid.uuid4().hex[:8]}"


def code_fingerprint(*parts: str) -> str:
    """Stable hash of the transformation logic identifiers for versioning."""
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


@dataclass
class LineageRecord:
    run_id: str
    job: str
    layer_from: str
    layer_to: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    rows_in: int = 0
    rows_out: int = 0
    rows_rejected: int = 0
    code_version: str = ""
    started_at: str = field(default_factory=_utcnow_iso)
    finished_at: str | None = None
    status: str = "running"
    metrics: dict[str, Any] = field(default_factory=dict)

    def complete(self, status: str = "success") -> "LineageRecord":
        self.finished_at = _utcnow_iso()
        self.status = status
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)
