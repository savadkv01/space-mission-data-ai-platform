"""GEE Sentinel-2 connectors use injected metadata/statistics functions offline."""

import pytest

from ingestion.api.gee_sentinel2 import (
    GeeSentinel2IndexConnector,
    GeeSentinel2SceneConnector,
)
from transformation.batch.bronze_to_silver import silver_index, silver_scene


def _canned_stats(**kwargs):
    return {
        "mean": 0.42, "min": 0.1, "max": 0.8, "stDev": 0.12,
        "sampleCount": 75, "noDataCount": 25,
    }


def test_scene_connector_stamps_stac_metadata_and_event_time():
    seen = {}

    def scene_fn(**kwargs):
        seen.update(kwargs)
        return [{
            "type": "Feature",
            "id": "S2A_20261029",
            "collection": "sentinel-2-l2a",
            "bbox": kwargs["bbox"],
            "properties": {
                "datetime": "2026-10-29T07:02:45Z",
                "eo:cloud_cover": 19.5,
                "platform": "sentinel-2",
                "provider": "Google Earth Engine",
            },
        }]

    connector = GeeSentinel2SceneConnector(scene_fn=scene_fn)
    envelope = connector.ingest(
        bbox=[54.9, 24.8, 55.6, 25.4],
        datetime_range="2026-10-20T00:00:00Z/2026-10-30T23:59:59Z",
        limit=10,
    )[0]
    assert envelope._source == "SENTINELHUB"
    assert envelope._event_ts == "2026-10-29T07:02:45Z"
    assert envelope.payload["collection"] == "sentinel-2-l2a"
    assert seen["limit"] == 10
    silver_record = dict(envelope.payload, _source=envelope._source)
    assert silver_scene([silver_record]).rows[0]["cloud_cover"] == 19.5


def test_index_connector_emits_silver_compatible_buckets():
    connector = GeeSentinel2IndexConnector(stats_fn=_canned_stats)
    envelope = connector.ingest(
        index="NDVI", bbox=[54.9, 24.8, 55.6, 25.4],
        datetime_range="2026-10-29T00:00:00Z/2026-10-29T23:59:59Z",
    )[0]
    assert envelope._source == "SENTINELHUB_STATS"
    assert envelope._event_ts == "2026-10-29T00:00:00Z"
    assert envelope.payload["collection"] == "COPERNICUS/S2_SR_HARMONIZED"
    result = silver_index([envelope.payload])
    assert len(result.rows) == 1
    assert result.rows[0]["valid_pixel_fraction"] == 0.75


def test_index_connector_rejects_unknown_index():
    with pytest.raises(ValueError, match="unknown index"):
        GeeSentinel2IndexConnector(stats_fn=_canned_stats).ingest(index="AOD")


def test_scene_connector_rejects_nonpositive_limit():
    with pytest.raises(ValueError, match="limit must be positive"):
        GeeSentinel2SceneConnector(scene_fn=lambda **kwargs: []).ingest(limit=0)
