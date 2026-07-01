"""Landsat 8/9 connector via the public USGS LandsatLook STAC API.

Queries the LandsatLook STAC search endpoint for Collection-2 scene **metadata**
(no auth required for search), providing the long historical optical baseline
that Sentinel-2 alone cannot for UC-14 change detection. One Bronze record per
STAC feature; conforms to ``obs_scene`` in Silver like other imagery metadata.
Docs: https://landsatlook.usgs.gov/stac-server/
"""

from __future__ import annotations

from typing import Any

from ingestion.api.base import ApiConnector


class LandsatConnector(ApiConnector):
    source_code = "LANDSAT"
    rate_limit_per_s = 2

    SEARCH_URL = "https://landsatlook.usgs.gov/stac-server/search"

    def fetch_raw(self, *, collections: tuple[str, ...] = ("landsat-c2l2-sr",),
                  bbox: list[float] | None = None,
                  datetime_range: str = "2024-01-01T00:00:00Z/2024-01-31T23:59:59Z",
                  limit: int = 20, **_: Any) -> tuple[list[dict[str, Any]], str]:
        body = {
            "collections": list(collections),
            "bbox": bbox or [54.8, 24.8, 55.6, 25.5],  # Dubai-ish AOI
            "datetime": datetime_range,
            "limit": limit,
        }
        data = self.http.post_json(self.SEARCH_URL, json=body)
        features = data.get("features", []) if isinstance(data, dict) else []
        return features, "json"

    def _event_ts(self, record: dict[str, Any]) -> str | None:
        props = record.get("properties", {}) if isinstance(record, dict) else {}
        return props.get("datetime")
