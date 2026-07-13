"""Sentinel Hub **Statistical API** connector — OAuth client credentials.

Unlike :class:`SentinelHubConnector` (which lands scene *metadata* into
``obs_scene``), this connector lands *aggregated band-index statistics* per AOI
per time bucket. Each response bucket becomes one Bronze record feeding the
Silver ``obs_index`` entity and the EO feature store (UC-14 NDVI change,
UC-15 NBR burn severity, UC-16 NDWI water extent).

The OAuth token flow and credentials are inherited from
:class:`SentinelHubConnector`. Endpoint verified in the pre-flight tool.
Docs: https://docs.sentinel-hub.com/api/latest/api/statistical/
"""

from __future__ import annotations

from typing import Any

from ingestion.api.sentinelhub import SentinelHubConnector


def _evalscript(formula: str) -> str:
    """Build a VERSION=3 evalscript exposing a single ``index`` output band.

    ``formula`` is a JS expression over the sampled ``s`` bands (e.g.
    ``(s.B08 - s.B04) / (s.B08 + s.B04)``). A ``dataMask`` output band is always
    emitted so the Statistical API can report valid vs no-data pixel counts.
    """
    return (
        "//VERSION=3\n"
        "function setup() {\n"
        '  return {\n'
        '    input: [{ bands: ["B03", "B04", "B08", "B12", "dataMask"] }],\n'
        '    output: [\n'
        '      { id: "index", bands: 1 },\n'
        '      { id: "dataMask", bands: 1 }\n'
        "    ]\n"
        "  };\n"
        "}\n"
        "function evaluatePixel(s) {\n"
        f"  let v = {formula};\n"
        "  return { index: [v], dataMask: [s.dataMask] };\n"
        "}\n"
    )


class SentinelHubStatsConnector(SentinelHubConnector):
    source_code = "SENTINELHUB_STATS"
    rate_limit_per_s = 2

    STATS_URL = "https://services.sentinel-hub.com/api/v1/statistics"

    #: Vegetation / water / burn indices as band-math evalscripts.
    EVALSCRIPTS = {
        "NDVI": _evalscript("(s.B08 - s.B04) / (s.B08 + s.B04)"),
        "NDWI": _evalscript("(s.B03 - s.B08) / (s.B03 + s.B08)"),
        "NBR": _evalscript("(s.B08 - s.B12) / (s.B08 + s.B12)"),
    }

    def fetch_raw(self, *, index: str = "NDVI",
                  bbox: list[float] | None = None,
                  datetime_range: str = "2024-06-01T00:00:00Z/2024-06-30T23:59:59Z",
                  aggregation_interval: str = "P1D",
                  collection: str = "sentinel-2-l2a",
                  resolution: float = 0.0001,
                  **_: Any) -> tuple[list[dict[str, Any]], str]:
        index_name = index.upper()
        if index_name not in self.EVALSCRIPTS:
            raise ValueError(
                f"unknown index {index!r}; choose from {sorted(self.EVALSCRIPTS)}"
            )
        aoi = bbox or [54.8, 24.8, 55.6, 25.5]  # Dubai-ish AOI
        buckets = self._request_stats(
            evalscript=self.EVALSCRIPTS[index_name],
            bbox=aoi,
            datetime_range=datetime_range,
            aggregation_interval=aggregation_interval,
            collection=collection,
            resolution=resolution,
        )
        # Statistical buckets carry no AOI/index context; stamp the request
        # parameters onto each record so the Silver cleaner can key them.
        records: list[dict[str, Any]] = []
        for bucket in buckets:
            if isinstance(bucket, dict):
                enriched = dict(bucket)
                enriched["index"] = index_name
                enriched["bbox"] = aoi
                enriched["collection"] = collection
                records.append(enriched)
        return records, "json"

    def _request_stats(self, *, evalscript: str, bbox: list[float],
                       datetime_range: str, aggregation_interval: str,
                       collection: str, resolution: float) -> list[dict[str, Any]]:
        """POST an evalscript to the Statistical API and return the raw buckets.

        Shared by every stats-based subclass (NDVI/NDWI/NBR here, TROPOMI trace
        gases, MODIS/VIIRS AOD). Handles OAuth, RFC3339 time bounds, and the
        output-raster resolution cap. The ``data`` array of per-time-bucket
        aggregates is returned verbatim; callers stamp source-specific context.
        """
        time_from, _, time_to = datetime_range.partition("/")
        time_from = self._rfc3339(time_from, end=False)
        time_to = self._rfc3339(time_to or time_from, end=True)
        # The Statistical API caps the output raster at ~2500 px per side; for a
        # geographic (EPSG:4326) request the resolution is in degrees, so a wide
        # AOI at native spacing would exceed the cap and return HTTP 400.
        # Auto-coarsen resx/resy to keep each dimension within the budget.
        resx, resy = self._safe_resolution(bbox, resolution)
        token = self._access_token()
        body = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                    },
                },
                "data": [{"type": collection}],
            },
            "aggregation": {
                "timeRange": {"from": time_from, "to": time_to or time_from},
                "aggregationInterval": {"of": aggregation_interval},
                "evalscript": evalscript,
                "resx": resx,
                "resy": resy,
            },
        }
        headers = {"Authorization": f"Bearer {token}"}
        data = self.http.post_json(self.STATS_URL, json=body, headers=headers)
        return data.get("data", []) if isinstance(data, dict) else []

    def _event_ts(self, record: dict[str, Any]) -> str | None:
        interval = record.get("interval") if isinstance(record, dict) else None
        if isinstance(interval, dict):
            return interval.get("from")
        return None

    #: Statistical API output raster limit (pixels per side) with headroom.
    MAX_DIM_PX = 2500

    @staticmethod
    def _rfc3339(value: str, *, end: bool) -> str:
        """Coerce a date or timestamp to a full RFC3339 instant with ``Z``.

        The Statistical API rejects date-only bounds (HTTP 400); a bare
        ``YYYY-MM-DD`` is expanded to the start/end of that day.
        """
        text = (value or "").strip()
        if not text:
            return text
        if "T" not in text:
            text += "T23:59:59Z" if end else "T00:00:00Z"
        elif not text.endswith("Z") and "+" not in text:
            text += "Z"
        return text

    def _safe_resolution(self, bbox: list[float], resolution: float) -> tuple[float, float]:
        """Return ``(resx, resy)`` degrees that keep the raster within the cap."""
        width = abs(bbox[2] - bbox[0])
        height = abs(bbox[3] - bbox[1])
        resx = max(resolution, width / self.MAX_DIM_PX) if width else resolution
        resy = max(resolution, height / self.MAX_DIM_PX) if height else resolution
        return resx, resy
