"""Google Earth Engine Sentinel-2 metadata and spectral-index connectors.

These connectors preserve the existing Sentinel Hub Bronze source codes and
payload contracts while using the configured GEE service account. This allows
scene metadata and AOI-level indices to keep refreshing when a Sentinel Hub
account is unavailable.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from ingestion.api.gee import EarthEngineStatsConnector

SceneFn = Callable[..., list[dict[str, Any]]]


def _recent_range() -> str:
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=14)
    end = today - timedelta(days=1)
    return f"{start.isoformat()}T00:00:00Z/{end.isoformat()}T23:59:59Z"


class GeeSentinel2SceneConnector(EarthEngineStatsConnector):
    """Land recent Sentinel-2 scene metadata in the Silver-compatible STAC shape."""

    source_code = "SENTINELHUB"
    COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"

    def __init__(self, scene_fn: SceneFn | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._scene_fn = scene_fn

    def fetch_raw(self, *, bbox: list[float] | None = None,
                  datetime_range: str | None = None, limit: int = 20,
                  **_: Any) -> tuple[list[dict[str, Any]], str]:
        if limit < 1:
            raise ValueError("limit must be positive")
        aoi = bbox or [54.9, 24.8, 55.6, 25.4]
        date_range = datetime_range or _recent_range()
        if self._scene_fn is not None:
            features = self._scene_fn(
                bbox=aoi, datetime_range=date_range, limit=limit,
                collection=self.COLLECTION,
            )
        else:
            features = self._fetch_scenes(aoi, date_range, limit)
        return features, "json"

    def _fetch_scenes(self, bbox: list[float], datetime_range: str,
                      limit: int) -> list[dict[str, Any]]:
        ee = self._ee_client()
        self._ensure_init()
        time_from, _, time_to = datetime_range.partition("/")
        geometry = ee.Geometry.Rectangle(bbox)
        collection = (ee.ImageCollection(self.COLLECTION)
                      .filterDate(time_from, time_to)
                      .filterBounds(geometry)
                      .sort("system:time_start", False))
        images = collection.limit(limit).toList(limit)
        features = ee.FeatureCollection(images.map(
            lambda image: ee.Feature(
                None,
                ee.Image(image).toDictionary(
                    ["system:time_start", "CLOUDY_PIXEL_PERCENTAGE"]
                ).set("scene_id", ee.Image(image).get("system:index")),
            )
        )).getInfo().get("features", [])

        records: list[dict[str, Any]] = []
        for feature in features:
            properties = feature.get("properties") or {}
            timestamp_ms = properties.get("system:time_start")
            scene_id = properties.get("scene_id")
            if timestamp_ms is None or not scene_id:
                continue
            timestamp = datetime.fromtimestamp(
                timestamp_ms / 1000, tz=timezone.utc
            ).isoformat().replace("+00:00", "Z")
            records.append({
                "type": "Feature",
                "id": scene_id,
                "collection": "sentinel-2-l2a",
                "bbox": bbox,
                "properties": {
                    "datetime": timestamp,
                    "eo:cloud_cover": properties.get("CLOUDY_PIXEL_PERCENTAGE"),
                    "platform": "sentinel-2",
                    "provider": "Google Earth Engine",
                },
            })
        return records

    def _event_ts(self, record: dict[str, Any]) -> str | None:
        properties = record.get("properties") or {}
        return properties.get("datetime")


def index_band_order(index: str) -> list[str]:
    """Band list for ``ee.Image.normalizedDifference``, which computes
    ``(first - second) / (first + second)``."""
    return list(GeeSentinel2IndexConnector.INDEX_BANDS[index.upper()])


class GeeSentinel2IndexConnector(EarthEngineStatsConnector):
    """Calculate daily, cloud-masked Sentinel-2 NDVI, NDWI, or NBR statistics."""

    source_code = "SENTINELHUB_STATS"
    COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
    SCALE_M = 250.0
    #: ``(first, second)`` for ``(first - second) / (first + second)``:
    #: NDVI = (NIR - Red), NDWI (McFeeters) = (Green - NIR), NBR = (NIR - SWIR2).
    INDEX_BANDS = {
        "NDVI": ("B8", "B4"),
        "NDWI": ("B3", "B8"),
        "NBR": ("B8", "B12"),
    }
    #: v1 (before 2026-11-14) passed the bands to ``normalizedDifference`` in
    #: reverse, publishing the negated index. Silver quarantines unversioned
    #: records from this collection as superseded.
    FORMULA_VERSION = 2

    def fetch_raw(self, *, index: str = "NDVI",
                  bbox: list[float] | None = None,
                  datetime_range: str | None = None,
                  **_: Any) -> tuple[list[dict[str, Any]], str]:
        index_name = index.upper()
        if index_name not in self.INDEX_BANDS:
            raise ValueError(
                f"unknown index {index!r}; choose from {sorted(self.INDEX_BANDS)}"
            )
        aoi = bbox or [54.9, 24.8, 55.6, 25.4]
        buckets = self._daily_buckets(
            band=index_name,
            collection=self.COLLECTION,
            bbox=aoi,
            datetime_range=datetime_range or _recent_range(),
        )
        records = []
        for bucket in buckets:
            enriched = dict(bucket)
            enriched.update({
                "index": index_name,
                "bbox": aoi,
                "collection": self.COLLECTION,
                "formula_version": self.FORMULA_VERSION,
            })
            records.append(enriched)
        return records, "json"

    def _ee_reduce_region(self, *, band: str, collection: str,
                          bbox: list[float], time_from: str,
                          time_to: str) -> dict[str, Any] | None:
        ee = self._ee_client()
        self._ensure_init()
        geometry = ee.Geometry.Rectangle(bbox)
        images = (ee.ImageCollection(collection)
                  .filterDate(time_from, time_to)
                  .filterBounds(geometry))

        def add_index(image: Any) -> Any:
            image = ee.Image(image)
            scl = image.select("SCL")
            clear = (scl.neq(0).And(scl.neq(1)).And(scl.neq(3))
                     .And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
                     .And(scl.neq(11)))
            return (image.normalizedDifference(index_band_order(band))
                    .rename("index").updateMask(clear))

        indexed = images.map(add_index)
        if not indexed.size().getInfo():
            return None
        image = indexed.mean().rename("index")
        return self._summarize_image(image, geometry, ee)
