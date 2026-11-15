"""Regional AOI ingestion (INDIA tier) for the daily driver and backfills.

One plan per region (``settings.climate.region_sources``) keeps request volume
bounded: FIRMS per AOI box (not a national rectangle) with a fixed detection cap,
PM-only OpenAQ with station/page caps, and AOI-scoped GEE statistics. Any cap
that truncates data is returned as ``coverage = capped`` so incomplete coverage
is visible in run metadata instead of silently reading as complete.

Backfill (one-off, operator run inside the Airflow container):

    python -m ingestion.scripts.regional_ingest --region INDIA --days 30

FIRMS-only gap backfill (e.g. after a sensor switch), including extra boxes:

    python -m ingestion.scripts.regional_ingest --region INDIA --only firms \
        --start 2026-11-03 --end 2026-11-13 --extra-firms-area uae_gulf=30,10,60,40
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable

from ingestion.batch.ingest_task import run_connector_to_bronze
from ingestion.config.settings import settings

#: OpenAQ per-AOI quota for dense station networks (laptop + rate-limit budget).
OPENAQ_MAX_LOCATIONS = 25
OPENAQ_LIMIT = 200
OPENAQ_MAX_PAGES = 3


def _run(results: dict[str, Any], key: str, fn: Callable[[], dict[str, Any]]) -> None:
    try:
        results[key] = fn()
    except Exception as exc:  # noqa: BLE001 - one bad source must not abort the region
        results[key] = {"error": str(exc)}


def firms_windows(start: date, end: date, max_days: int = 5) -> list[tuple[str, int]]:
    """Split ``[start, end]`` into FIRMS ``(date, day_range)`` request windows."""
    windows = []
    cursor = start
    while cursor <= end:
        days = min(max_days, (end - cursor).days + 1)
        windows.append((cursor.isoformat(), days))
        cursor += timedelta(days=days)
    return windows


def ingest_region(region: str, start: date, end: date, *,
                  firms_backfill: bool = False,
                  sources: tuple[str, ...] | None = None) -> dict[str, Any]:
    """Land one region's sources for ``[start, end]`` (UTC dates) in Bronze.

    ``firms_backfill=False`` requests the latest day only (daily run);
    ``True`` walks ``[start, end]`` in 5-day historical windows. ``sources``
    restricts the run to a subset of the plan's source names.
    """
    plan = settings.climate.region_sources.get(region)
    if plan is None:
        raise KeyError(f"no source plan for region {region!r}")
    if sources is not None:
        plan = {name: aois for name, aois in plan.items() if name in sources}
    climate = settings.climate
    results: dict[str, Any] = {}
    date_range = f"{start.isoformat()}T00:00:00Z/{end.isoformat()}T23:59:59Z"

    from ingestion.api.nasa_firms import FirmsConnector
    for aoi in plan.get("firms", ()):
        area = climate.firms_area(aoi)
        windows = firms_windows(start, end) if firms_backfill else [(None, 1)]
        for window_date, days in windows:
            suffix = f":{window_date}" if window_date else ""
            _run(results, f"FIRMS:{aoi}{suffix}", lambda a=area, d=window_date, n=days:
                 run_connector_to_bronze(
                     FirmsConnector(), source=climate.firms_source, area=a, days=n, date=d,
                     max_records=climate.firms_max_records_per_request))

    from ingestion.api.openaq import OpenAqConnector
    for aoi in plan.get("openaq", ()):
        _run(results, f"OPENAQ:{aoi}", lambda a=aoi: run_connector_to_bronze(
            OpenAqConnector(), aoi_id=a, pollutants=list(climate.openaq_pm_pollutants),
            date_from=start.isoformat(), date_to=end.isoformat(),
            limit=OPENAQ_LIMIT, max_pages=OPENAQ_MAX_PAGES,
            max_locations=OPENAQ_MAX_LOCATIONS))

    from ingestion.api.gee_s5p import GeeS5pConnector
    for aoi in plan.get("tropomi", ()):
        for product in climate.tropomi_products:
            _run(results, f"TROPOMI:{aoi}:{product}", lambda a=aoi, p=product:
                 run_connector_to_bronze(GeeS5pConnector(), aoi_id=a, product=p,
                                         datetime_range=date_range))

    from ingestion.api.gee_aod import GeeAodConnector
    for aoi in plan.get("aod", ()):
        _run(results, f"MODIS_AOD:{aoi}", lambda a=aoi: run_connector_to_bronze(
            GeeAodConnector(), aoi_id=a, sensor="MODIS", datetime_range=date_range))

    from ingestion.api.gee_sentinel2 import GeeSentinel2IndexConnector
    for index in ("ndvi", "ndwi"):
        for aoi in plan.get(index, ()):
            _run(results, f"SENTINELHUB_STATS:{index.upper()}:{aoi}", lambda a=aoi, i=index:
                 run_connector_to_bronze(GeeSentinel2IndexConnector(), index=i.upper(),
                                         bbox=climate.bbox(a), datetime_range=date_range))

    from ingestion.api.gfw_4wings import GFW_DATASETS, GfwAreaConnector
    gfw_start = end - timedelta(days=max(climate.gfw_lookback_days, (end - start).days + 1) - 1)
    for aoi in plan.get("gfw", ()):
        for dataset in GFW_DATASETS:
            _run(results, f"GFW_4WINGS:{aoi}:{dataset}", lambda a=aoi, d=dataset:
                 run_connector_to_bronze(GfwAreaConnector(), aoi_id=a, dataset=d,
                                         date_from=gfw_start.isoformat(), date_to=end.isoformat()))
    return results


def backfill_firms(areas: dict[str, str], start: date, end: date) -> dict[str, Any]:
    """FIRMS-only backfill of named request boxes over ``[start, end]`` (5-day windows)."""
    from ingestion.api.nasa_firms import FirmsConnector

    climate = settings.climate
    results: dict[str, Any] = {}
    for name, area in areas.items():
        for window_date, days in firms_windows(start, end):
            _run(results, f"FIRMS:{name}:{window_date}", lambda a=area, d=window_date, n=days:
                 run_connector_to_bronze(
                     FirmsConnector(), source=climate.firms_source, area=a, days=n, date=d,
                     max_records=climate.firms_max_records_per_request))
    return results


def main(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(description="Regional AOI ingestion / backfill")
    parser.add_argument("--region", default="INDIA")
    parser.add_argument("--days", type=int, default=30, help="backfill window ending yesterday (UTC)")
    parser.add_argument("--start", help="explicit start date (YYYY-MM-DD); overrides --days")
    parser.add_argument("--end", help="explicit end date (YYYY-MM-DD); default yesterday")
    parser.add_argument("--only", choices=("all", "firms", "gfw"), default="all")
    parser.add_argument("--extra-firms-area", action="append", default=[], metavar="NAME=W,S,E,N",
                        help="additional FIRMS request box (FIRMS-only mode)")
    args = parser.parse_args(argv)
    end = date.fromisoformat(args.end) if args.end else (
        datetime.now(timezone.utc).date() - timedelta(days=1))
    start = date.fromisoformat(args.start) if args.start else end - timedelta(days=args.days - 1)
    if args.only == "firms":
        plan = settings.climate.region_sources.get(args.region, {})
        areas = {aoi: settings.climate.firms_area(aoi) for aoi in plan.get("firms", ())}
        areas.update(dict(item.split("=", 1) for item in args.extra_firms_area))
        return backfill_firms(areas, start, end)
    if args.only == "gfw":
        plan = settings.climate.region_sources.get(args.region, {})
        return ingest_region(args.region, start, end, firms_backfill=False,
                             sources=("gfw",)) if plan.get("gfw") else {}
    return ingest_region(args.region, start, end, firms_backfill=True)


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, default=str))
