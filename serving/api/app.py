"""FastAPI serving API — STUB for Phase 16.

This is a thin, read-only contract sketch over the serving data products. It is
intentionally minimal: real data access, OIDC auth, caching, and deployment are
implemented in Phase 16 (API & Application layer). FastAPI is imported lazily so
this module (and the offline test suite) never hard-depends on it.

Run locally once FastAPI is installed:
    uvicorn serving.api.app:app --reload
"""

from __future__ import annotations

from typing import Any, Protocol


class ServingRepository(Protocol):
    """Read-only access to serving products (implemented in Phase 16).

    A concrete implementation queries the DuckDB / lakehouse serving schema; the
    protocol keeps the API decoupled from the storage engine.
    """

    def wildfire(self, **filters: Any) -> list[dict[str, Any]]: ...
    def flood(self, **filters: Any) -> list[dict[str, Any]]: ...
    def vessels(self, **filters: Any) -> list[dict[str, Any]]: ...
    def scenes(self, **filters: Any) -> list[dict[str, Any]]: ...
    def validation(self, **filters: Any) -> list[dict[str, Any]]: ...


def create_app(repo: ServingRepository | None = None):  # pragma: no cover - Phase 16
    """Build the FastAPI app. Imported lazily so this file loads without FastAPI."""
    try:
        from fastapi import FastAPI, Query
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "FastAPI is not installed. The serving API is stubbed for Phase 16; "
            "install fastapi/uvicorn to run it."
        ) from exc

    app = FastAPI(title="Space Mission Serving API", version="v1")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/analytics/wildfire")
    def wildfire(aoi_key: str | None = Query(default=None),
                 severity: str | None = Query(default=None),
                 limit: int = Query(default=50, le=500)) -> dict[str, Any]:
        if repo is None:
            return {"data": [], "meta": {"note": "stub — wire ServingRepository in Phase 16"}}
        data = repo.wildfire(aoi_key=aoi_key, severity=severity)[:limit]
        return {"data": data, "meta": {"count": len(data)}}

    return app


# Module-level ``app`` for ``uvicorn serving.api.app:app`` — stays None-repo until
# Phase 16 provides a concrete ServingRepository.
try:  # pragma: no cover - only exercised when FastAPI is installed
    app = create_app()
except RuntimeError:  # FastAPI absent (default in the offline dev venv)
    app = None
