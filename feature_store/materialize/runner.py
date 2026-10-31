from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from typing import Any

from feast import FeatureStore

from feature_store.database import connect
from feature_store.readiness import FEATURE_READINESS, may_materialize

REPO_PATH = Path(
    os.environ.get(
        "FEAST_REPO_PATH",
        str(Path(__file__).parents[1] / "feature_repo"),
    )
)
if str(REPO_PATH) not in sys.path:
    sys.path.insert(0, str(REPO_PATH))

from feature_views import FEATURE_VIEWS  # noqa: E402


@dataclass(frozen=True)
class MaterializationResult:
    view: str
    status: str
    rows_available: int
    detail: str


def _view_table(view_name: str) -> str:
    return {
        "satellite_health_daily": "source_satellite_health",
        "mission_operations": "source_mission_operations",
        "orbit_stability": "source_orbit_stability",
        "launch_performance_monthly": "source_launch_performance",
        "space_weather_daily": "source_space_weather",
        "wildfire_aoi_daily": "source_wildfire_aoi_daily",
        "spectral_index_daily": "source_spectral_index_daily",
        "scene_catalog_metadata": "source_scene_catalog",
        "vessel_activity_daily": "source_vessel_activity",
        "air_quality_aoi_daily": "source_air_quality_daily",
        "dust_aoi_daily": "source_dust_daily",
        "climate_indicator_aoi_daily": "source_climate_indicator_daily",
        "vegetation_health_aoi_daily": "source_vegetation_health_daily",
    }[view_name]


def _source_window(view_name: str, readiness_status: str) -> tuple[int, datetime, datetime]:
    table = _view_table(view_name)
    with connect() as connection:
        row = connection.execute(
            f"""
            SELECT COUNT(*), MIN(event_timestamp), MAX(event_timestamp)
            FROM feast.{table}
            WHERE readiness_status = %s
            """,
            (readiness_status,),
        ).fetchone()
    count, start, end = row
    if not count or start is None or end is None:
        return 0, datetime.now(timezone.utc), datetime.now(timezone.utc)
    return count, start, end + timedelta(microseconds=1)


def materialize_eligible(
    store: FeatureStore,
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    incremental: bool = False,
) -> list[MaterializationResult]:
    allow_demo = os.environ.get("FEATURE_STORE_DEMO_SEED", "false").lower() == "true"
    allow_restricted = (
        os.environ.get("FEATURE_STORE_ALLOW_RESTRICTED", "false").lower() == "true"
    )
    results: list[MaterializationResult] = []
    for view in FEATURE_VIEWS:
        readiness = FEATURE_READINESS[view.name]
        if not may_materialize(
            readiness.status,
            allow_demo=allow_demo,
            allow_restricted=allow_restricted,
        ):
            results.append(
                MaterializationResult(
                    view=view.name,
                    status="blocked",
                    rows_available=0,
                    detail=readiness.blocker,
                )
            )
            continue

        rows_available, source_start, source_end = _source_window(
            view.name, readiness.status
        )
        if not rows_available:
            results.append(
                MaterializationResult(
                    view=view.name,
                    status="no_data",
                    rows_available=0,
                    detail="No eligible source rows exist; no materialization was attempted.",
                )
            )
            continue

        if incremental:
            store.materialize_incremental(
                end_date=end_date or datetime.now(timezone.utc),
                feature_views=[view.name],
            )
        else:
            store.materialize(
                start_date=start_date or source_start,
                end_date=end_date or source_end,
                feature_views=[view.name],
            )
        results.append(
            MaterializationResult(
                view=view.name,
                status=readiness.status,
                rows_available=rows_available,
                detail="Materialized within the declared readiness scope.",
            )
        )
    return results


def materialize_report(
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    incremental: bool = False,
) -> list[dict[str, Any]]:
    if start_date and end_date and start_date >= end_date:
        raise ValueError("start_date must be earlier than end_date.")
    store = FeatureStore(repo_path=str(REPO_PATH))
    return [
        asdict(result)
        for result in materialize_eligible(
            store,
            start_date=start_date,
            end_date=end_date,
            incremental=incremental,
        )
    ]
