"""Full-run batch API ingestion driver — lands every configured source in Bronze.

Manual/operator entry point for a full-platform live run (see OPERATIONS.md
§10). Intentionally lives outside the Makefile/DAG surface: DAGs remain the
canonical *scheduled* orchestration, this script is the one-shot "ingest
everything now" helper used when validating the whole platform end to end.

Run inside the ingestion runner container (needs Kafka+MinIO+internet):
    docker exec ingest-runner python -m ingestion.scripts.run_full_batch_ingest

The driver uses rolling recent windows for latency-sensitive sources
(NASA POWER, OpenAQ, TROPOMI, MODIS/VIIRS AOD). Real-time feeds (SWPC,
CelesTrak, FIRMS NRT, GFW) use live data. Optical scene metadata and indices
use Google Earth Engine.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from ingestion.batch.ingest_task import run_connector_to_bronze
from ingestion.config.settings import settings


def main() -> dict:
    results: dict[str, dict] = {}

    # Keep recurring full runs operational; sources with publication latency
    # can still return their latest available observations within this window.
    today = datetime.now(timezone.utc).date()
    recent_start = (today - timedelta(days=14)).isoformat()
    recent_end = (today - timedelta(days=1)).isoformat()
    recent_range = f"{recent_start}T00:00:00Z/{recent_end}T23:59:59Z"

    # --- real-time / anonymous sources (Phase 8) -----------------------------
    from ingestion.api.noaa_swpc import SwpcConnector
    try:
        results["SWPC"] = run_connector_to_bronze(SwpcConnector())
    except Exception as exc:  # noqa: BLE001 - report and continue (one bad source
        results["SWPC"] = {"error": str(exc)}  # shouldn't abort the whole run

    from ingestion.api.celestrak import CelestrakConnector
    try:
        results["CELESTRAK"] = run_connector_to_bronze(CelestrakConnector())
    except Exception as exc:  # noqa: BLE001
        results["CELESTRAK"] = {"error": str(exc)}

    from ingestion.api.nasa_power import PowerConnector
    for aoi_id, bbox in settings.climate.aois.items():
        latitude = (bbox[1] + bbox[3]) / 2
        longitude = (bbox[0] + bbox[2]) / 2
        result_key = "POWER" if aoi_id == "AOI-DXB" else f"POWER:{aoi_id}"
        try:
            results[result_key] = run_connector_to_bronze(
                PowerConnector(), latitude=latitude, longitude=longitude, aoi_id=aoi_id,
                start=recent_start.replace("-", ""), end=recent_end.replace("-", ""),
            )
        except Exception as exc:  # noqa: BLE001
            results[result_key] = {"error": str(exc)}

    # --- keyed MVP Earth-observation sources (Phase 8) -----------------------
    # UAE-GULF FIRMS stays one broad request (the regional envelope sits inside it).
    from ingestion.api.nasa_firms import FirmsConnector
    try:
        results["FIRMS"] = run_connector_to_bronze(
            FirmsConnector(), source=settings.climate.firms_source, area="30,10,60,40",
            days=settings.climate.firms_daily_day_range,
        )
    except Exception as exc:  # noqa: BLE001
        results["FIRMS"] = {"error": str(exc)}

    from ingestion.api.gfw import GfwConnector
    try:
        results["GFW"] = run_connector_to_bronze(GfwConnector())
    except Exception as exc:  # noqa: BLE001
        results["GFW"] = {"error": str(exc)}

    from ingestion.api.gee_sentinel2 import GeeSentinel2SceneConnector
    try:
        results["SENTINELHUB"] = run_connector_to_bronze(
            GeeSentinel2SceneConnector(), bbox=settings.climate.bbox("AOI-DXB"),
            datetime_range=recent_range, limit=20,
        )
    except Exception as exc:  # noqa: BLE001
        results["SENTINELHUB"] = {"error": str(exc)}

    # --- climate + regional sources: one per-region plan for UAE-GULF and INDIA
    # (OpenAQ, TROPOMI and MODIS AOD via GEE, Sentinel-2 NDVI/NDWI, GFW 4Wings,
    # and per-AOI FIRMS for INDIA). See settings.climate.region_sources.
    from ingestion.scripts.regional_ingest import ingest_region
    for region in settings.climate.region_sources:
        results.update(ingest_region(
            region, date.fromisoformat(recent_start), date.fromisoformat(recent_end)))

    return results


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, default=str))
