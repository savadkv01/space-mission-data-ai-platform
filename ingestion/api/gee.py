"""Google Earth Engine (GEE) statistical connector base — free S-5P / AOD access.

Free alternative to the Sentinel Hub Statistical API for the two atmospheric
sources whose collections are **not** entitled on the free/CDSE Sentinel Hub
plan (Sentinel-5P trace gases, MODIS/VIIRS AOD). GEE is free for
non-commercial / research use and indexes **both** ``COPERNICUS/S5P/*`` and
``MODIS/*`` collections, so it fills the entitlement gap without paying for a
commercial Sentinel Hub subscription.

Design goal: emit Bronze records in the **identical Statistical-API bucket
shape** the existing Silver cleaners already consume
(:func:`transformation.cleaning.climate.buckets.bucket_stats`) so that
``clean_atmos_column`` / ``clean_aerosol`` and every Gold / serving / BI layer
downstream keep working unchanged. Each day of the requested range becomes one
bucket::

    {"interval": {"from": ..., "to": ...},
     "outputs": {"index": {"bands": {"B0": {"stats": {
         "mean", "min", "max", "stDev", "sampleCount", "noDataCount"}}}}}}

Testability: the GEE-specific ``reduceRegion`` call is isolated behind an
injectable ``stats_fn`` seam (mirroring how the HTTP connectors inject
``HttpClient``). Offline unit tests inject a canned ``stats_fn`` and never import
the heavy ``earthengine-api`` SDK; the real SDK is imported lazily only on a
live run. Auth uses a Google service-account JSON key.

Docs: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Callable

from ingestion.api.base import ApiConnector
from ingestion.config.settings import settings

#: Signature of the injectable per-day statistics provider.
StatsFn = Callable[..., "dict[str, Any] | None"]


class EarthEngineStatsConnector(ApiConnector):
    """Base for GEE-backed AOI-statistics connectors (one bucket per day).

    Subclasses set the image collection / band and stamp source-specific
    context (product, unit, sensor) onto each bucket, exactly like the Sentinel
    Hub ``*StatsConnector`` subclasses do.
    """

    source_code = "GEE"
    rate_limit_per_s = 2

    #: ``reduceRegion`` sampling scale in metres (subclass tunes to native res).
    SCALE_M: float = 1000.0
    #: Multiplier applied to raw band values (e.g. MODIS AOD stores value*1000).
    VALUE_SCALE: float = 1.0
    #: Cap on ``reduceRegion`` pixels (bestEffort coarsens beyond this).
    MAX_PIXELS: float = 1e9

    def __init__(self, stats_fn: StatsFn | None = None, ee_module: Any = None,
                 project: str | None = None, service_account: str | None = None,
                 key_file: str | None = None, http=None) -> None:
        super().__init__(http)
        self._stats_fn = stats_fn
        self._ee = ee_module
        self._project = project or settings.credentials.gee_project
        self._service_account = service_account or settings.credentials.gee_service_account
        self._key_file = key_file or settings.credentials.gee_key_file
        self._initialized = False

    # -- envelope hook -----------------------------------------------------
    def _event_ts(self, record: dict[str, Any]) -> str | None:
        interval = record.get("interval") if isinstance(record, dict) else None
        if isinstance(interval, dict):
            return interval.get("from")
        return None

    # -- daily bucket builder ---------------------------------------------
    def _daily_buckets(self, *, band: str, collection: str,
                       bbox: list[float], datetime_range: str) -> list[dict[str, Any]]:
        """Iterate the range one UTC day at a time, emitting SH-stats buckets.

        Days with no imagery over the AOI are skipped (``stats_fn`` returns
        ``None``) so gaps stay visible rather than landing zero-filled rows.
        """
        start_s, _, end_s = datetime_range.partition("/")
        start = self._parse_day(start_s)
        end = self._parse_day(end_s or start_s)
        stats_fn = self._stats_fn or self._ee_reduce_region

        buckets: list[dict[str, Any]] = []
        day = start
        while day <= end:
            nxt = day + timedelta(days=1)
            d_from = day.strftime("%Y-%m-%dT00:00:00Z")
            d_to = nxt.strftime("%Y-%m-%dT00:00:00Z")
            stats = stats_fn(band=band, collection=collection, bbox=bbox,
                             time_from=d_from, time_to=d_to)
            if stats and stats.get("mean") is not None:
                buckets.append({
                    "interval": {"from": d_from, "to": d_to},
                    "outputs": {"index": {"bands": {"B0": {"stats": stats}}}},
                })
            day = nxt
        return buckets

    @staticmethod
    def _parse_day(text: str) -> datetime:
        return datetime.strptime((text or "").strip()[:10], "%Y-%m-%d")

    # -- live GEE seam (not exercised by offline tests) -------------------
    def _ee_client(self) -> Any:
        if self._ee is None:
            try:
                import ee  # type: ignore
            except ImportError as exc:  # pragma: no cover - env-dependent
                raise RuntimeError(
                    "earthengine-api not installed; `pip install earthengine-api` "
                    "to use the Google Earth Engine connectors"
                ) from exc
            self._ee = ee
        return self._ee

    def _ensure_init(self) -> None:  # pragma: no cover - requires GEE creds
        if self._initialized:
            return
        ee = self._ee_client()
        if self._service_account and self._key_file:
            creds = ee.ServiceAccountCredentials(self._service_account, self._key_file)
            ee.Initialize(creds, project=self._project or None)
        else:
            # Fall back to application-default / cached interactive credentials.
            ee.Initialize(project=self._project or None)
        self._initialized = True

    def _ee_reduce_region(self, *, band: str, collection: str,
                          bbox: list[float], time_from: str,
                          time_to: str) -> dict[str, Any] | None:  # pragma: no cover
        """Real GEE ``reduceRegion`` over the AOI for one day. Live path only."""
        ee = self._ee_client()
        self._ensure_init()
        geom = ee.Geometry.Rectangle(bbox)
        coll = (ee.ImageCollection(collection)
                .filterDate(time_from, time_to)
                .filterBounds(geom)
                .select([band]))
        if not coll.size().getInfo():
            return None
        img = coll.mean().rename("index")
        return self._summarize_image(img, geom, ee)

    def _summarize_image(self, image: Any, geometry: Any, ee: Any) -> dict[str, Any] | None:
        """Reduce a one-band image to the common daily statistics contract."""
        reducer = (ee.Reducer.mean()
                   .combine(ee.Reducer.minMax(), sharedInputs=True)
                   .combine(ee.Reducer.stdDev(), sharedInputs=True)
                   .combine(ee.Reducer.count(), sharedInputs=True))
        raw = image.reduceRegion(reducer=reducer, geometry=geometry, scale=self.SCALE_M,
                                 bestEffort=True, maxPixels=self.MAX_PIXELS).getInfo() or {}
        mean = raw.get("index_mean")
        if mean is None:
            return None
        total = (ee.Image.constant(1).reduceRegion(
            reducer=ee.Reducer.count(), geometry=geometry, scale=self.SCALE_M,
            bestEffort=True, maxPixels=self.MAX_PIXELS).getInfo() or {})
        valid = int(raw.get("index_count") or 0)
        total_px = int(total.get("constant") or 0)
        nodata = max(total_px - valid, 0)
        s = self.VALUE_SCALE

        def _scale(v: Any) -> Any:
            return v * s if isinstance(v, (int, float)) else v

        return {
            "mean": _scale(mean),
            "min": _scale(raw.get("index_min")),
            "max": _scale(raw.get("index_max")),
            "stDev": _scale(raw.get("index_stdDev")),
            "sampleCount": valid,
            "noDataCount": nodata,
        }
