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
        if all(isinstance(row, dict) for row in rows):
            records = rows
        elif isinstance(rows[0], list):
            header, *data = rows
            records = [dict(zip(header, row)) for row in data]
        else:
            raise ValueError("unexpected NOAA SWPC planetary K-index response shape")

        return [self._normalize_record(record) for record in records], "json"

    @classmethod
    def _normalize_record(cls, record: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(record)
        timestamp = cls._normalize_timestamp(record.get("time_tag") or record.get("timestamp"))
        if timestamp:
            normalized["timestamp"] = timestamp
        kp_index = record.get("Kp", record.get("kp", record.get("kp_index")))
        if kp_index is not None:
            normalized["kp_index"] = kp_index
        return normalized

    @staticmethod
    def _normalize_timestamp(value: Any) -> str | None:
        if not value:
            return None
        timestamp = str(value).strip().replace(" ", "T")
        if timestamp.endswith("Z") or "+" in timestamp:
            return timestamp
        return f"{timestamp}Z"

    def _event_ts(self, record: dict[str, Any]) -> str | None:
        return self._normalize_timestamp(record.get("timestamp") or record.get("time_tag"))
