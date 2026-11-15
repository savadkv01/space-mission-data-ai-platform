"""Global Fishing Watch 4Wings area connector — requires ``GFW_API_TOKEN``.

Replaces the identity name-search sample (``gfw.py``) as the maritime activity
source. For one AOI polygon it requests a **spatially aggregated** daily 4Wings
report, grouped by flag state, for three public datasets:

* ``fishing_effort`` — apparent fishing hours from AIS (published ~96 h behind)
* ``presence``       — AIS vessel presence hours, all vessel types
* ``sar``            — Sentinel-1 radar vessel detections (~5 days behind);
  detections with an empty flag have no matching AIS broadcast (candidate
  "dark" vessels)

Server-side aggregation keeps the grain at AOI × day × flag (the Gulf over 30
days is ~4k rows instead of ~180k grid cells), which fits the laptop budget.
``vessel_count`` is the distinct vessels for that flag and day inside the AOI.
GFW APIs are free for non-commercial use only.

Docs: https://globalfishingwatch.org/our-apis/documentation/docs/v3/4wings
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from ingestion.api.base import ApiConnector
from ingestion.config.settings import settings

#: Platform dataset name -> GFW 4Wings dataset id.
GFW_DATASETS = {
    "fishing_effort": "public-global-fishing-effort:latest",
    "presence": "public-global-presence:latest",
    "sar": "public-global-sar-presence:latest",
}


class GfwAreaConnector(ApiConnector):
    source_code = "GFW_4WINGS"
    rate_limit_per_s = 1

    REPORT_URL = "https://gateway.api.globalfishingwatch.org/v3/4wings/report"

    def __init__(self, http=None, token: str | None = None) -> None:
        super().__init__(http)
        self.token = token or settings.credentials.gfw_api_token

    def fetch_raw(self, *, aoi_id: str, dataset: str, date_from: str, date_to: str,
                  bbox: list[float] | None = None, **_: Any) -> tuple[list[dict[str, Any]], str]:
        if not self.token:
            raise RuntimeError("GFW_API_TOKEN is not configured")
        if dataset not in GFW_DATASETS:
            raise ValueError(f"unknown GFW dataset {dataset!r}; choose from {sorted(GFW_DATASETS)}")
        w, s, e, n = bbox or settings.climate.bbox(aoi_id)
        query = urlencode({
            "spatial-resolution": "LOW",
            "temporal-resolution": "DAILY",
            "datasets[0]": GFW_DATASETS[dataset],
            "date-range": f"{date_from},{date_to}",
            "format": "JSON",
            "group-by": "FLAG",
            "spatial-aggregation": "true",
        })
        body = {"geojson": {"type": "Polygon",
                            "coordinates": [[[w, s], [e, s], [e, n], [w, n], [w, s]]]}}
        data = self.http.post_json(f"{self.REPORT_URL}?{query}", json=body,
                                   headers={"Authorization": f"Bearer {self.token}"})
        records = []
        for entry in (data or {}).get("entries", []):
            for version, rows in entry.items():
                for row in rows or []:
                    records.append({
                        "date": row.get("date"),
                        "flag": row.get("flag") or None,
                        "hours": row.get("hours"),
                        "detections": row.get("detections"),
                        "vessel_count": row.get("vesselIDs"),
                        "dataset": dataset,
                        "gfw_dataset_version": version,
                        "aoi_id": aoi_id,
                        "bbox": [w, s, e, n],
                        "date_from": date_from,
                        "date_to": date_to,
                    })
        return records, "json"

    def _event_ts(self, record: dict[str, Any]) -> str | None:
        date = record.get("date")
        return f"{date}T00:00:00Z" if date else None
