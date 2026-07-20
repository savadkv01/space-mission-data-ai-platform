"""Superset REST API client for the BI-refresh pipeline stage. Plain
``requests`` (already installed for ingestion connectors); no Superset SDK
dependency.
"""

from __future__ import annotations

from typing import Any

from pipelines.config.settings import settings


class SupersetClient:
    def __init__(self, base_url: str | None = None, user: str | None = None, password: str | None = None) -> None:
        self.base_url = (base_url or settings.superset.base_url).rstrip("/")
        self.user = user or settings.superset.admin_user
        self.password = password or settings.superset.admin_password
        self._session = None
        self._access_token: str | None = None

    def _client(self):
        import requests  # lazy import

        if self._session is None:
            self._session = requests.Session()
        return requests, self._session

    def login(self) -> None:
        requests, session = self._client()
        resp = session.post(
            f"{self.base_url}/api/v1/security/login",
            json={"username": self.user, "password": self.password, "provider": "db", "refresh": True},
            timeout=30,
        )
        resp.raise_for_status()
        self._access_token = resp.json()["access_token"]

    def _headers(self) -> dict[str, str]:
        if self._access_token is None:
            self.login()
        return {"Authorization": f"Bearer {self._access_token}"}

    def list_datasets(self) -> list[dict[str, Any]]:
        _, session = self._client()
        resp = session.get(
            f"{self.base_url}/api/v1/dataset/",
            params={"q": "(page_size:100)"},
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["result"]

    def refresh_dataset(self, dataset_id: int) -> bool:
        """Refresh a dataset's column metadata (``PUT /dataset/{id}/refresh``).

        Falls back to a lightweight existence check (``GET /dataset/{id}``) if
        the refresh action isn't available on the running Superset version, so
        the BI stage still verifies the dataset is reachable either way.
        """
        _, session = self._client()
        resp = session.put(
            f"{self.base_url}/api/v1/dataset/{dataset_id}/refresh",
            headers=self._headers(),
            timeout=60,
        )
        if resp.status_code in (404, 405):
            resp = session.get(
                f"{self.base_url}/api/v1/dataset/{dataset_id}",
                headers=self._headers(),
                timeout=30,
            )
        resp.raise_for_status()
        return True
