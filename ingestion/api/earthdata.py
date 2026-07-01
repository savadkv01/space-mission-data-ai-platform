"""NASA Earthdata CMR granule-discovery connector.

Queries the public Common Metadata Repository (CMR) granule search API for
scene/granule **metadata** (no download, no auth) to seed the catalog and the
UC-25 metadata-quality use case. Landsat and MODIS granules are discoverable
here by ``short_name``.
Docs: https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html
"""

from __future__ import annotations

from typing import Any

from ingestion.api.base import ApiConnector


class EarthdataConnector(ApiConnector):
    source_code = "EARTHDATA"
    rate_limit_per_s = 2

    SEARCH_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"

    def fetch_raw(self, *, short_name: str = "MOD14", bounding_box: str = "-10,-10,10,10",
                  temporal: str | None = None, page_size: int = 20,
                  **_: Any) -> tuple[list[dict[str, Any]], str]:
        params = {
            "short_name": short_name,
            "bounding_box": bounding_box,
            "page_size": str(page_size),
        }
        if temporal:
            params["temporal"] = temporal
        data = self.http.get_json(self.SEARCH_URL, params=params)
        feed = data.get("feed", {}) if isinstance(data, dict) else {}
        entries = feed.get("entry", []) if isinstance(feed, dict) else []
        return entries, "json"

    def _event_ts(self, record: dict[str, Any]) -> str | None:
        return record.get("time_start")
