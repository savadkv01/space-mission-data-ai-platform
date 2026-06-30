"""NOAA SWPC space-weather connector — anonymous (verified in pre-flight).

Pulls the planetary K-index product. Docs: https://services.swpc.noaa.gov/
"""

from __future__ import annotations

from typing import Any

from ingestion.api.base import ApiConnector


class SwpcConnector(ApiConnector):
    source_code = "SWPC"
    rate_limit_per_s = 3

    KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"

    def fetch_raw(self, **_: Any) -> tuple[list[dict[str, Any]], str]:
        rows = self.http.get_json(self.KP_URL)
        if not rows or not isinstance(rows, list):
            return [], "json"
        header, *data = rows  # first row is the column header
        records = [dict(zip(header, row)) for row in data]
        return records, "json"

    def _event_ts(self, record: dict[str, Any]) -> str | None:
        ts = record.get("time_tag")
        return f"{ts.replace(' ', 'T')}Z" if ts else None
