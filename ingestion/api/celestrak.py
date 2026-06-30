"""CelesTrak TLE/GP connector — anonymous (verified in pre-flight).

Pulls General Perturbations element sets. Docs: https://celestrak.org/NORAD/elements/
"""

from __future__ import annotations

from typing import Any

from ingestion.api.base import ApiConnector


class CelestrakConnector(ApiConnector):
    source_code = "CELESTRAK"
    rate_limit_per_s = 1  # respect CelesTrak fair-use

    GP_URL = "https://celestrak.org/NORAD/elements/gp.php"

    def fetch_raw(self, *, group: str = "stations", **_: Any) -> tuple[list[dict[str, Any]], str]:
        # JSON format gives structured GP records directly.
        params = {"GROUP": group, "FORMAT": "json"}
        data = self.http.get_json(self.GP_URL, params=params)
        records = data if isinstance(data, list) else []
        return records, "json"

    def _event_ts(self, record: dict[str, Any]) -> str | None:
        epoch = record.get("EPOCH")
        return f"{epoch}Z" if epoch and not str(epoch).endswith("Z") else epoch
