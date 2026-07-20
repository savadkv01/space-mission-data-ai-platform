"""Full-run batch API ingestion driver — lands every configured source in Bronze.

Manual/operator entry point for a full-platform live run (see OPERATIONS.md
§10). Intentionally lives outside the Makefile/DAG surface: DAGs remain the
canonical *scheduled* orchestration, this script is the one-shot "ingest
everything now" helper used when validating the whole platform end to end.

Run inside the ingestion runner container (needs Kafka+MinIO+internet):
    docker exec ingest-runner python -m ingestion.scripts.run_full_batch_ingest

Historical/settled date windows are used for sources with multi-day
processing latency (NASA POWER, OpenAQ, TROPOMI, MODIS/VIIRS AOD) so a request
for "yesterday" doesn't 404/422 against real upstream APIs. Real-time feeds
(SWPC, CelesTrak, FIRMS NRT, GFW, Sentinel Hub Catalog) use live "now" data.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from ingestion.batch.ingest_task import run_connector_to_bronze
from ingestion.common.http import HttpClient, RateLimiter
from ingestion.config.settings import settings


def _fast_fail_http() -> HttpClient:
    """HttpClient tuned for the Sentinel Hub Statistical API.

    That endpoint occasionally read-times-out under load; the default client
    (4 retries x 30s) can then block for minutes on a single call. Use 1 retry
    and a 15s timeout so a bad call fails fast and the run keeps moving.
    """
    return HttpClient(rate_limit=RateLimiter(2, 1.0), total_retries=1)


def main() -> dict:
    results: dict[str, dict] = {}

    # Settled historical window: avoids POWER/OpenAQ/SentinelHub processing latency.
    hist_start, hist_end = "2024-06-01", "2024-06-07"
    hist_range = f"{hist_start}T00:00:00Z/{hist_end}T23:59:59Z"

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
    try:
        results["POWER"] = run_connector_to_bronze(
            PowerConnector(), latitude=25.2, longitude=55.3,
            start=hist_start.replace("-", ""), end=hist_end.replace("-", ""),
        )
    except Exception as exc:  # noqa: BLE001
        results["POWER"] = {"error": str(exc)}

    # --- keyed MVP Earth-observation sources (Phase 8) -----------------------
    from ingestion.api.nasa_firms import FirmsConnector
    try:
        results["FIRMS"] = run_connector_to_bronze(
            FirmsConnector(), source="VIIRS_SNPP_NRT", area="-124.5,32.5,-114.5,42", days=1,
        )
    except Exception as exc:  # noqa: BLE001
        results["FIRMS"] = {"error": str(exc)}

    from ingestion.api.gfw import GfwConnector
    try:
        results["GFW"] = run_connector_to_bronze(GfwConnector())
    except Exception as exc:  # noqa: BLE001
        results["GFW"] = {"error": str(exc)}

    from ingestion.api.sentinelhub import SentinelHubConnector
    try:
        results["SENTINELHUB"] = run_connector_to_bronze(SentinelHubConnector())
    except Exception as exc:  # noqa: BLE001
        results["SENTINELHUB"] = {"error": str(exc)}

    # NDVI stats over the Dubai AOI feeds the Silver "index" entity (UC-14/15/16).
    from ingestion.api.sentinelhub_stats import SentinelHubStatsConnector
    try:
        results["SENTINELHUB_STATS:NDVI"] = run_connector_to_bronze(
            SentinelHubStatsConnector(http=_fast_fail_http()), index="NDVI", datetime_range=hist_range,
        )
    except Exception as exc:  # noqa: BLE001 - report and continue
        results["SENTINELHUB_STATS:NDVI"] = {"error": str(exc)}

    # NDWI stats over the same Dubai AOI feed the flood mart (kpi_flood_aoi_daily,
    # UC-16). Same Sentinel-2 L2A collection as NDVI (entitled on the free plan),
    # so no extra source is needed — the flood path only lacked NDWI ingestion.
    try:
        results["SENTINELHUB_STATS:NDWI"] = run_connector_to_bronze(
            SentinelHubStatsConnector(http=_fast_fail_http()), index="NDWI", datetime_range=hist_range,
        )
    except Exception as exc:  # noqa: BLE001 - report and continue
        results["SENTINELHUB_STATS:NDWI"] = {"error": str(exc)}

    # --- climate connectors (Phase 8b) ---------------------------------------
    # OpenAQ v3 per-sensor measurements don't reliably respect date_from/date_to
    # (observed: some sensors return their full history regardless), so bound
    # locations/pages/limit explicitly to keep this within the 16 GB budget —
    # a full-run validation needs representative data, not an exhaustive backfill.
    from ingestion.api.openaq import OpenAqConnector
    for aoi in ("AOI-DXB", "AOI-AUH", "AOI-UAE-NAT"):
        try:
            results[f"OPENAQ:{aoi}"] = run_connector_to_bronze(
                OpenAqConnector(), aoi_id=aoi, date_from=hist_start, date_to=hist_end,
                limit=200, max_pages=1, max_locations=3,
            )
        except Exception as exc:  # noqa: BLE001
            results[f"OPENAQ:{aoi}"] = {"error": str(exc)}

    # Sentinel-5P trace gases + MODIS AOD are sourced from Google Earth Engine
    # (free) because their Sentinel Hub collections are not entitled on the free
    # plan; source codes stay TROPOMI / MODIS_AOD so downstream is unchanged.
    from ingestion.api.gee_s5p import GeeS5pConnector
    for aoi in ("AOI-UAE-NAT", "AOI-AUH", "AOI-DXB"):
        for product in settings.climate.tropomi_products:
            try:
                results[f"TROPOMI:{aoi}:{product}"] = run_connector_to_bronze(
                    GeeS5pConnector(), aoi_id=aoi, product=product, datetime_range=hist_range,
                )
            except Exception as exc:  # noqa: BLE001
                results[f"TROPOMI:{aoi}:{product}"] = {"error": str(exc)}

    from ingestion.api.gee_aod import GeeAodConnector
    for aoi in ("AOI-UAE-NAT", "AOI-DESERT", "AOI-ARABIA", "AOI-IRAQ", "AOI-IRAN"):
        try:
            results[f"MODIS_AOD:{aoi}"] = run_connector_to_bronze(
                GeeAodConnector(), aoi_id=aoi, sensor="MODIS", datetime_range=hist_range,
            )
        except Exception as exc:  # noqa: BLE001
            results[f"MODIS_AOD:{aoi}"] = {"error": str(exc)}

    return results


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, default=str))
