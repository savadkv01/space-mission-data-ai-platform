"""NASA POWER daily weather connector — anonymous (verified in pre-flight).

Docs: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
"""

from __future__ import annotations

from typing import Any

from ingestion.api.base import ApiConnector


class PowerConnector(ApiConnector):
    source_code = "POWER"
    rate_limit_per_s = 3

    URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

    def fetch_raw(self, *, latitude: float = 25.20, longitude: float = 55.27,
                  start: str = "20240101", end: str = "20240107",
                  parameters: str = "T2M,RH2M,WS2M,PRECTOTCORR", **_: Any
                  ) -> tuple[list[dict[str, Any]], str]:
        params = {
            "parameters": parameters,
            "community": "RE",
            "latitude": latitude,
            "longitude": longitude,
            "start": start,
            "end": end,
            "format": "JSON",
        }
        data = self.http.get_json(self.URL, params=params)
        # Flatten the POWER nested structure into one record per (date, param).
        props = data.get("properties", {}).get("parameter", {})
        records: list[dict[str, Any]] = []
        for param, series in props.items():
            for date, value in series.items():
                records.append({
                    "date": date,
                    "parameter": param,
                    "value": value,
                    "latitude": latitude,
                    "longitude": longitude,
                })
        return records, "json"

    def _event_ts(self, record: dict[str, Any]) -> str | None:
        date = record.get("date")
        return f"{date[:4]}-{date[4:6]}-{date[6:]}T00:00:00Z" if date and len(date) == 8 else None
