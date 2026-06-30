"""Sentinel Hub connector — requires OAuth2 client credentials.

Authenticates with ``SENTINELHUB_CLIENT_ID`` / ``SENTINELHUB_CLIENT_SECRET``
(client-credentials grant), then queries the Catalog (STAC) API for scene
**metadata** — not pixels — landing one Bronze record per STAC feature
(UC-14/15). Token + endpoints verified in the pre-flight tool.
Docs: https://docs.sentinel-hub.com/api/latest/api/catalog/
"""

from __future__ import annotations

from typing import Any

from ingestion.api.base import ApiConnector
from ingestion.config.settings import settings


class SentinelHubConnector(ApiConnector):
    source_code = "SENTINELHUB"
    rate_limit_per_s = 2

    TOKEN_URL = "https://services.sentinel-hub.com/oauth/token"
    CATALOG_URL = "https://services.sentinel-hub.com/api/v1/catalog/1.0.0/search"

    def __init__(self, http=None, client_id: str | None = None,
                 client_secret: str | None = None) -> None:
        super().__init__(http)
        self.client_id = client_id or settings.credentials.sentinelhub_client_id
        self.client_secret = client_secret or settings.credentials.sentinelhub_client_secret
        self._token: str | None = None

    def _access_token(self) -> str:
        if self._token:
            return self._token
        if not (self.client_id and self.client_secret):
            raise RuntimeError("SENTINELHUB_CLIENT_ID/SECRET are not configured")
        payload = self.http.post_json(
            self.TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        self._token = payload["access_token"]
        return self._token

    def fetch_raw(self, *, collection: str = "sentinel-2-l2a",
                  bbox: list[float] | None = None,
                  datetime_range: str = "2024-01-01T00:00:00Z/2024-01-31T23:59:59Z",
                  limit: int = 20, **_: Any) -> tuple[list[dict[str, Any]], str]:
        token = self._access_token()
        body = {
            "collections": [collection],
            "bbox": bbox or [54.8, 24.8, 55.6, 25.5],  # Dubai-ish AOI
            "datetime": datetime_range,
            "limit": limit,
        }
        headers = {"Authorization": f"Bearer {token}"}
        data = self.http.post_json(self.CATALOG_URL, json=body, headers=headers)
        features = data.get("features", []) if isinstance(data, dict) else []
        return features, "json"

    def _event_ts(self, record: dict[str, Any]) -> str | None:
        props = record.get("properties", {}) if isinstance(record, dict) else {}
        return props.get("datetime")
