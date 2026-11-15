import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import psycopg
from fastapi.testclient import TestClient

from feature_store.api import app as feature_api
from feature_store.api.cache import FeatureResponseCache


def test_feature_cache_serves_fresh_and_explicitly_stale_values():
    cache = FeatureResponseCache(ttl_seconds=0.01, stale_seconds=0.1)
    cache.put("key", {"value": 1})
    fresh, is_stale = cache.get("key")
    assert fresh == {"value": 1}
    assert not is_stale

    time.sleep(0.02)
    cached, is_stale = cache.get("key", allow_stale=True)
    assert cached == {"value": 1}
    assert is_stale

    time.sleep(0.1)
    expired, is_stale = cache.get("key", allow_stale=True)
    assert expired is None
    assert not is_stale


def test_readiness_endpoint_discloses_blockers_and_use_limits():
    response = TestClient(feature_api.app).get("/readiness")
    assert response.status_code == 200
    assert response.json()["as_of"] == feature_api.READINESS_AS_OF
    readiness = {item["view"]: item for item in response.json()["features"]}
    assert readiness["scene_catalog_metadata"]["allowed_use"] == "catalog_discovery_only"
    assert readiness["wildfire_aoi_daily"]["status"] == "blocked"
    assert readiness["air_quality_aoi_daily"]["sla_hours"] == 24
    assert readiness["air_quality_aoi_daily"]["publication_sla_minutes"] == 60
    assert readiness["dust_aoi_daily"]["status"] == "blocked"
    assert readiness["climate_indicator_aoi_daily"]["status"] == "blocked"
    assert readiness["vegetation_health_aoi_daily"]["status"] == "blocked"


def test_online_endpoint_rejects_blocked_feature_views_before_database_access():
    response = TestClient(feature_api.app).post(
        "/features/online",
        json={
            "feature_refs": ["wildfire_aoi_daily:max_frp"],
            "entity_rows": [{"aoi_key": "AOI-001"}],
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"]["features"][0]["work_package"] == "WP1"


def test_online_endpoint_keeps_climate_features_blocked_before_database_access():
    response = TestClient(feature_api.app).post(
        "/features/online",
        json={
            "feature_refs": ["air_quality_aoi_daily:pm25_mean"],
            "entity_rows": [{"aoi_key": "AOI-001"}],
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"]["features"][0]["work_package"] == "WP3"


def test_online_endpoint_reports_stale_scene_metadata(monkeypatch):
    class _Job:
        def to_dict(self):
            return {
                "cloud_cover": [35.4],
                "feature_date": ["2024-01-23"],
            }

    class _Store:
        def get_online_features(self, *, features, entity_rows):
            return _Job()

    monkeypatch.setattr(feature_api, "_cache", FeatureResponseCache())
    monkeypatch.setattr(feature_api, "_store", lambda: _Store())
    response = TestClient(feature_api.app).post(
        "/features/online",
        json={
            "feature_refs": [
                "scene_catalog_metadata:cloud_cover",
                "scene_catalog_metadata:feature_date",
            ],
            "entity_rows": [{"scene_key": "SCENE-TEST"}],
        },
    )
    assert response.status_code == 200
    assert response.json()["freshness"][0]["status"] == "stale"


def test_online_endpoint_reports_freshness_per_feature_view(monkeypatch):
    class _Job:
        def to_dict(self):
            now = datetime.now(timezone.utc)
            return {
                "air_quality_aoi_daily__pm25_mean": [12.0],
                "air_quality_aoi_daily__feature_date": [
                    (now - timedelta(minutes=30)).isoformat()
                ],
                "air_quality_aoi_daily__source_published_at": [
                    (now - timedelta(minutes=30)).isoformat()
                ],
                "dust_aoi_daily__aod_mean": [0.8],
                # Beyond the 96-hour dust objective (MAIAC publication lag).
                "dust_aoi_daily__feature_date": [
                    (now - timedelta(hours=120)).isoformat()
                ],
            }

    class _Store:
        def get_online_features(self, *, features, entity_rows):
            return _Job()

    readiness = dict(feature_api.FEATURE_READINESS)
    readiness["air_quality_aoi_daily"] = replace(
        readiness["air_quality_aoi_daily"],
        status="restricted",
    )
    readiness["dust_aoi_daily"] = replace(
        readiness["dust_aoi_daily"],
        status="restricted",
    )
    monkeypatch.setattr(feature_api, "FEATURE_READINESS", readiness)
    monkeypatch.setattr(feature_api, "_cache", FeatureResponseCache())
    monkeypatch.setattr(feature_api, "_store", lambda: _Store())

    response = TestClient(feature_api.app).post(
        "/features/online",
        json={
            "feature_refs": [
                "air_quality_aoi_daily:pm25_mean",
                "dust_aoi_daily:aod_mean",
            ],
            "entity_rows": [{"aoi_key": "AOI-001"}],
        },
    )

    freshness = {item["view"]: item for item in response.json()["freshness"]}
    assert response.status_code == 200
    assert freshness["air_quality_aoi_daily"]["status"] == "within_sla"
    assert freshness["air_quality_aoi_daily"]["publication_status"] == "within_sla"
    assert freshness["dust_aoi_daily"]["status"] == "stale"
    assert set(response.json()["features"]) == {
        "air_quality_aoi_daily__pm25_mean",
        "dust_aoi_daily__aod_mean",
    }


def test_online_endpoint_marks_cached_fallback_as_degraded(monkeypatch):
    class _Job:
        def to_dict(self):
            return {
                "health_score": [0.8],
                "feature_date": ["2026-10-31"],
            }

    class _Store:
        def get_online_features(self, *, features, entity_rows):
            return _Job()

    monkeypatch.setattr(
        feature_api,
        "_cache",
        FeatureResponseCache(ttl_seconds=0.01, stale_seconds=0.2),
    )
    monkeypatch.setattr(feature_api, "_store", lambda: _Store())
    client = TestClient(feature_api.app)
    request = {
        "feature_refs": [
            "satellite_health_daily:health_score",
            "satellite_health_daily:feature_date",
        ],
        "entity_rows": [{"sat_key": "SIM-SAT-001"}],
    }

    assert client.post("/features/online", json=request).json()["degraded"] is False
    time.sleep(0.02)

    def unavailable_store():
        raise psycopg.OperationalError("test-only connection failure")

    monkeypatch.setattr(feature_api, "_store", unavailable_store)
    fallback = client.post("/features/online", json=request)
    assert fallback.status_code == 200
    assert fallback.json()["cache"] == "stale_fallback"
    assert fallback.json()["degraded"] is True
