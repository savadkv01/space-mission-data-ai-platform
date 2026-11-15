from __future__ import annotations

import hmac
import os
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

import psycopg
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from feature_store.api.cache import FeatureResponseCache, cache_key
from feature_store.database import connect
from feature_store.materialize.gold_sync import sync_enabled_gold_sources
from feature_store.materialize.runner import materialize_report
from feature_store.readiness import FEATURE_READINESS, READINESS_AS_OF

app = FastAPI(title="Space Mission Feature Store", version="1.0.0")
_CLIMATE_FEATURE_VIEWS = {
    "air_quality_aoi_daily",
    "dust_aoi_daily",
    "climate_indicator_aoi_daily",
    "vegetation_health_aoi_daily",
}
_cache = FeatureResponseCache(
    ttl_seconds=float(os.environ.get("FEATURE_STORE_CACHE_TTL_SECONDS", "2")),
    stale_seconds=float(os.environ.get("FEATURE_STORE_CACHE_STALE_SECONDS", "60")),
)


class OnlineFeatureRequest(BaseModel):
    feature_refs: list[str] = Field(min_length=1, max_length=50)
    entity_rows: list[dict[str, Any]] = Field(min_length=1, max_length=500)


class MaterializationRequest(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    incremental: bool = True


@lru_cache(maxsize=1)
def _store():
    from feast import FeatureStore

    return FeatureStore(
        repo_path=os.environ.get(
            "FEAST_REPO_PATH",
            str(os.path.join(os.path.dirname(__file__), "..", "feature_repo")),
        )
    )


def _view_names(feature_refs: list[str]) -> list[str]:
    names = []
    for reference in feature_refs:
        view_name, separator, field_name = reference.partition(":")
        if not separator or not view_name or not field_name:
            raise HTTPException(
                status_code=422,
                detail=f"Feature references must use 'feature_view:field' format: {reference!r}",
            )
        if view_name not in FEATURE_READINESS:
            raise HTTPException(status_code=404, detail=f"Unknown feature view: {view_name}")
        if view_name not in names:
            names.append(view_name)
    return names


def _readiness_payload(view_names: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "view": (entry := FEATURE_READINESS[name]).view,
            "status": entry.status,
            "allowed_use": entry.use,
            "blocker": entry.blocker,
            "work_package": entry.work_package,
            "sla_hours": entry.max_age_hours,
            "publication_sla_minutes": entry.publication_sla_minutes,
        }
        for name in view_names
    ]


def _field_values(
    feature_values: dict[str, Any],
    *,
    view_name: str,
    field_name: str,
    allow_unqualified: bool,
) -> list[Any]:
    accepted_names = {
        f"{view_name}:{field_name}",
        f"{view_name}__{field_name}",
    }
    if allow_unqualified:
        accepted_names.add(field_name)
    return [
        value
        for result_name, values in feature_values.items()
        if result_name in accepted_names
        for value in values
    ]


def _freshness_payload(
    feature_refs: list[str],
    feature_values: dict[str, Any],
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    report = []
    view_names = _view_names(feature_refs)
    for name in view_names:
        entry = FEATURE_READINESS[name]
        dates = _field_values(
            feature_values,
            view_name=name,
            field_name="feature_date",
            allow_unqualified=len(view_names) == 1,
        )
        observation_ages = []
        for raw_date in dates:
            if raw_date is None:
                continue
            parsed = datetime.fromisoformat(str(raw_date))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            observation_ages.append(
                max(
                    0.0,
                    (now - parsed.astimezone(timezone.utc)).total_seconds() / 3600,
                )
            )
        publication_ages = []
        if entry.publication_sla_minutes is not None:
            publication_dates = _field_values(
                feature_values,
                view_name=name,
                field_name="source_published_at",
                allow_unqualified=len(view_names) == 1,
            )
            for raw_date in publication_dates:
                if raw_date is None:
                    continue
                parsed = datetime.fromisoformat(str(raw_date))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                publication_ages.append(
                    max(
                        0.0,
                        (now - parsed.astimezone(timezone.utc)).total_seconds() / 60,
                    )
                )
        max_observation_age = max(observation_ages) if observation_ages else None
        max_publication_age = max(publication_ages) if publication_ages else None
        report.append(
            {
                "view": name,
                "max_observed_age_hours": max_observation_age,
                "sla_hours": entry.max_age_hours,
                "status": (
                    "unknown"
                    if max_observation_age is None
                    else "stale"
                    if max_observation_age > entry.max_age_hours
                    else "within_sla"
                ),
                "max_source_publication_age_minutes": max_publication_age,
                "publication_sla_minutes": entry.publication_sla_minutes,
                "publication_status": (
                    "not_applicable"
                    if entry.publication_sla_minutes is None
                    else "unknown"
                    if max_publication_age is None
                    else "stale"
                    if max_publication_age > entry.publication_sla_minutes
                    else "within_sla"
                ),
            }
        )
    return report


@app.get("/health")
def health() -> dict[str, str]:
    try:
        with connect() as connection:
            connection.execute("SELECT 1")
    except psycopg.Error as error:
        raise HTTPException(status_code=503, detail="PostgreSQL feature store is unavailable.") from error
    return {"status": "ok", "feature_store": "feast"}


@app.get("/readiness")
def readiness() -> dict[str, Any]:
    return {
        "as_of": READINESS_AS_OF,
        "features": _readiness_payload(list(FEATURE_READINESS)),
    }


@app.post("/features/online")
def get_online_features(request: OnlineFeatureRequest) -> dict[str, Any]:
    view_names = _view_names(request.feature_refs)
    blocked = [
        FEATURE_READINESS[name]
        for name in view_names
        if FEATURE_READINESS[name].status == "blocked"
    ]
    if blocked:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Feature retrieval is blocked by the analysis-readiness gate.",
                "features": [
                    {
                        "view": entry.view,
                        "work_package": entry.work_package,
                        "blocker": entry.blocker,
                    }
                    for entry in blocked
                ],
            },
        )

    payload = request.model_dump(mode="json")
    key = cache_key(payload)
    cached, stale = _cache.get(key)
    if cached is not None:
        cached["cache"] = "hit"
        cached["degraded"] = False
        return cached

    requested_refs = set(request.feature_refs)
    hidden_refs = []
    for name in view_names:
        fields = ["feature_date"]
        if name in _CLIMATE_FEATURE_VIEWS:
            fields.append("source_published_at")
        hidden_refs.extend(
            f"{name}:{field_name}"
            for field_name in fields
            if f"{name}:{field_name}" not in requested_refs
        )
    try:
        values = _store().get_online_features(
            features=[*request.feature_refs, *hidden_refs],
            entity_rows=request.entity_rows,
        ).to_dict()
    except (psycopg.Error, SQLAlchemyError) as error:
        fallback, is_stale = _cache.get(key, allow_stale=True)
        if fallback is None or not is_stale:
            raise HTTPException(
                status_code=503,
                detail="Online feature retrieval failed and no valid cached response is available.",
            ) from error
        fallback["cache"] = "stale_fallback"
        fallback["degraded"] = True
        fallback["fallback_reason"] = "PostgreSQL retrieval failed; cached response is explicitly stale."
        return fallback

    hidden_output_names = set()
    for reference in hidden_refs:
        view_name, _, field_name = reference.partition(":")
        hidden_output_names.update(
            {
                f"{view_name}__{field_name}",
                f"{view_name}:{field_name}",
            }
        )
        if len(view_names) == 1:
            hidden_output_names.add(field_name)
    visible_values = {
        field_name: field_values
        for field_name, field_values in values.items()
        if field_name not in hidden_output_names
    }
    response = {
        "features": visible_values,
        "readiness": _readiness_payload(view_names),
        "freshness": _freshness_payload(request.feature_refs, values),
        "served_at": datetime.now(timezone.utc).isoformat(),
        "cache": "miss",
        "degraded": False,
    }
    _cache.put(key, response)
    return response


@app.post("/internal/materialize")
def run_materialization(
    request: MaterializationRequest,
    x_feature_job_token: str | None = Header(default=None),
) -> dict[str, Any]:
    expected_token = os.environ.get("FEATURE_STORE_JOB_TOKEN", "")
    if not expected_token:
        raise HTTPException(status_code=503, detail="Feature materialization trigger is disabled.")
    if x_feature_job_token is None or not hmac.compare_digest(
        x_feature_job_token, expected_token
    ):
        raise HTTPException(status_code=403, detail="Invalid feature job token.")
    if request.start_date and request.end_date and request.start_date >= request.end_date:
        raise HTTPException(status_code=422, detail="start_date must be earlier than end_date.")

    gold_sync = (
        sync_enabled_gold_sources()
        if os.environ.get("FEATURE_STORE_LOAD_GOLD", "false").lower() == "true"
        else []
    )
    report = materialize_report(
        start_date=request.start_date,
        end_date=request.end_date,
        incremental=request.incremental and request.start_date is None,
    )
    return {"gold_sync": gold_sync, "materialization": report}
