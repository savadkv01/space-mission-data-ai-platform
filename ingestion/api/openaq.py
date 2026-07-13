"""OpenAQ v3 ground-station air-quality connector — free API key.

Lands one Bronze record per (station, parameter, timestamp) surface measurement
for the configured pollutants inside an AOI bounding box. This is the ground
truth / calibration source for the climate air-quality track (UC-C3); it pairs
with the satellite column densities from :class:`TropomiConnector`.

Auth: OpenAQ v3 requires a free API key sent as an ``X-API-Key`` header.
Endpoint verified in the pre-flight tool.

OpenAQ v3 has **no** flat "measurements in a bbox" endpoint (that was a v2
shape); measurements are fetched per-sensor. This connector therefore makes
two kinds of calls:
  1. ``GET /v3/locations?bbox=...`` — stations + their sensor list in the AOI.
  2. ``GET /v3/sensors/{sensor_id}/measurements`` — one call per matching
     sensor (station x pollutant), for the requested date window.
Docs: https://docs.openaq.org/
"""

from __future__ import annotations

from typing import Any

from ingestion.api.base import ApiConnector
from ingestion.config.settings import settings


class OpenAqConnector(ApiConnector):
    source_code = "OPENAQ"
    rate_limit_per_s = 2

    LOCATIONS_URL = "https://api.openaq.org/v3/locations"
    SENSOR_MEASUREMENTS_URL = "https://api.openaq.org/v3/sensors/{sensor_id}/measurements"

    def __init__(self, http=None, api_key: str | None = None) -> None:
        super().__init__(http)
        self.api_key = api_key or settings.credentials.openaq_api_key

    def fetch_raw(self, *, aoi_id: str = "AOI-DXB",
                  bbox: list[float] | None = None,
                  pollutants: list[str] | None = None,
                  date_from: str = "2024-06-01",
                  date_to: str = "2024-06-07",
                  limit: int = 1000,
                  max_pages: int = 5,
                  max_locations: int = 5,
                  **_: Any) -> tuple[list[dict[str, Any]], str]:
        aoi = bbox or settings.climate.bbox(aoi_id)
        params_list = list(pollutants or settings.climate.openaq_pollutants)
        headers = {"X-API-Key": self.api_key} if self.api_key else {}

        locations = self.http.get_json(
            self.LOCATIONS_URL,
            params={"bbox": ",".join(str(c) for c in aoi), "limit": max_locations},
            headers=headers,
        )
        stations = locations.get("results", []) if isinstance(locations, dict) else []

        records: list[dict[str, Any]] = []
        for station in stations:
            if not isinstance(station, dict):
                continue
            station_coords = station.get("coordinates") or {}
            for sensor in station.get("sensors", []) or []:
                pname = (sensor.get("parameter") or {}).get("name")
                sensor_id = sensor.get("id")
                if pname not in params_list or sensor_id is None:
                    continue
                page = 1
                while page <= max_pages:
                    data = self.http.get_json(
                        self.SENSOR_MEASUREMENTS_URL.format(sensor_id=sensor_id),
                        params={"date_from": date_from, "date_to": date_to,
                                "limit": limit, "page": page},
                        headers=headers,
                    )
                    results = data.get("results", []) if isinstance(data, dict) else []
                    if not results:
                        break
                    for result in results:
                        if isinstance(result, dict):
                            enriched = dict(result)
                            # The per-sensor measurement already carries its own
                            # {"parameter": {"name", "units", ...}} block; only
                            # backfill it if this endpoint/mock omits it.
                            enriched.setdefault("parameter", pname)
                            # Measurement "coordinates" is often null; fall back
                            # to the station's location.
                            if not enriched.get("coordinates"):
                                enriched["coordinates"] = station_coords
                            enriched["locationId"] = station.get("id")
                            enriched["sensorsId"] = sensor_id
                            enriched["station_name"] = station.get("name")
                            # Stamp request context so the Silver cleaner can key/tag by AOI.
                            enriched["aoi_id"] = aoi_id
                            enriched["bbox"] = aoi
                            records.append(enriched)
                    if len(results) < limit:
                        break
                    page += 1
        return records, "json"

    def _event_ts(self, record: dict[str, Any]) -> str | None:
        # Tolerant to v2/v3 shapes: date.utc, datetime.utc, period.datetimeFrom.utc.
        if not isinstance(record, dict):
            return None
        for key in ("date", "datetime", "period"):
            node = record.get(key)
            if isinstance(node, dict):
                ts = node.get("utc") or node.get("datetime_utc") or node.get("datetimeFrom")
                if isinstance(ts, dict):
                    ts = ts.get("utc")
                if ts:
                    return ts
        return record.get("datetime_utc") or record.get("datetime")

