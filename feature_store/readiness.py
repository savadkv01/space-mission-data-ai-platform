from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

ReadinessStatus = Literal["demo_only", "restricted", "blocked"]
_ALLOWED_STATUSES = {"demo_only", "restricted", "blocked"}


@dataclass(frozen=True)
class FeatureReadiness:
    view: str
    status: ReadinessStatus
    source: str
    blocker: str
    work_package: str
    use: str
    max_age_hours: int
    publication_sla_minutes: int | None


def load_readiness(path: Path | None = None) -> dict[str, FeatureReadiness]:
    manifest_path = path or Path(__file__).with_name("readiness.yaml")
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    entries: dict[str, FeatureReadiness] = {}
    for raw in manifest["features"]:
        status = raw["status"]
        if status not in _ALLOWED_STATUSES:
            raise ValueError(f"Unsupported readiness status {status!r} for {raw['view']}")
        view_name = raw["view"]
        if view_name in entries:
            raise ValueError(f"Duplicate readiness entry for {view_name}")
        entries[view_name] = FeatureReadiness(
            view=view_name,
            status=status,
            source=raw["source"],
            blocker=raw["blocker"],
            work_package=raw["work_package"],
            use=raw["use"],
            max_age_hours=int(raw["max_age_hours"]),
            publication_sla_minutes=(
                int(raw["publication_sla_minutes"])
                if raw.get("publication_sla_minutes") is not None
                else None
            ),
        )
    return entries


FEATURE_READINESS = load_readiness()


def may_materialize(status: str, *, allow_demo: bool, allow_restricted: bool) -> bool:
    if status == "demo_only":
        return allow_demo
    if status == "restricted":
        return allow_restricted
    return False
