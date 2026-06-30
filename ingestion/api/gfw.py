"""Global Fishing Watch (GFW) connector — requires ``GFW_API_TOKEN``.

Pulls vessel-identity records from the GFW API v3 (maritime domain awareness,
UC-18). Endpoint verified in the pre-flight tool.
Docs: https://globalfishingwatch.org/our-apis/documentation
"""

from __future__ import annotations

from typing import Any

from ingestion.api.base import ApiConnector
from ingestion.config.settings import settings


class GfwConnector(ApiConnector):
    source_code = "GFW"
    rate_limit_per_s = 2

    SEARCH_URL = "https://gateway.api.globalfishingwatch.org/v3/vessels/search"
    DEFAULT_DATASET = "public-global-vessel-identity:latest"

    def __init__(self, http=None, token: str | None = None) -> None:
        super().__init__(http)
        self.token = token or settings.credentials.gfw_api_token

    def fetch_raw(self, *, query: str = "Maria", limit: int = 20,
                  dataset: str | None = None, **_: Any) -> tuple[list[dict[str, Any]], str]:
        if not self.token:
            raise RuntimeError("GFW_API_TOKEN is not configured")
        params = {
            "query": query,
            "datasets[0]": dataset or self.DEFAULT_DATASET,
            "limit": str(limit),
        }
        headers = {"Authorization": f"Bearer {self.token}"}
        data = self.http.get_json(self.SEARCH_URL, params=params, headers=headers)
        if isinstance(data, dict):
            records = data.get("entries", [])
        elif isinstance(data, list):
            records = data
        else:
            records = []
        return records, "json"

    def _event_ts(self, record: dict[str, Any]) -> str | None:
        # Vessel identity records carry transmission date ranges, not a single
        # event time; surface the latest first-transmission date when present.
        reg = record.get("registryInfo") or record.get("selfReportedInfo") or []
        if isinstance(reg, list) and reg:
            ts = reg[0].get("transmissionDateFrom") or reg[0].get("firstTransmissionDate")
            return ts
        return None
