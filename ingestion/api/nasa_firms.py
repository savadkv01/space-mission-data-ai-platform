"""NASA FIRMS active-fire connector (also covers VIIRS).

Verified accessible in the pre-flight tool. Requires ``FIRMS_MAP_KEY``.
Docs: https://firms.modaps.eosdis.nasa.gov/api/area/
"""

from __future__ import annotations

from typing import Any

from ingestion.api.base import ApiConnector, parse_csv
from ingestion.config.settings import settings


class FirmsConnector(ApiConnector):
    source_code = "FIRMS"
    rate_limit_per_s = 2

    BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

    def __init__(self, http=None, map_key: str | None = None) -> None:
        super().__init__(http)
        self.map_key = map_key or settings.credentials.firms_map_key

    def fetch_raw(self, *, source: str = "VIIRS_SNPP_NRT", area: str = "-10,-10,10,10",
                  days: int = 1, **_: Any) -> tuple[list[dict[str, Any]], str]:
        if not self.map_key:
            raise RuntimeError("FIRMS_MAP_KEY is not configured")
        url = f"{self.BASE}/{self.map_key}/{source}/{area}/{days}"
        resp = self.http.get(url)
        resp.raise_for_status()
        text = resp.text
        if not text.lower().startswith("latitude"):
            self.log.warning("FIRMS returned no fire rows for area=%s", area)
            return [], "csv"
        return parse_csv(text), "csv"

    def _event_ts(self, record: dict[str, Any]) -> str | None:
        date = record.get("acq_date")
        time = str(record.get("acq_time", "")).zfill(4)
        if date:
            return f"{date}T{time[:2]}:{time[2:]}:00Z"
        return None
