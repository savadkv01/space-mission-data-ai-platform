"""GEE MODIS/VIIRS AOD connector tests — injected stats_fn, no GEE SDK."""

import pytest

from ingestion.api.gee_aod import GeeAodConnector


def _canned_stats(**kwargs):
    """AOD already in physical range (VALUE_SCALE applies only on the live path)."""
    return {
        "mean": 0.35, "min": 0.10, "max": 0.80, "stDev": 0.12,
        "sampleCount": 80, "noDataCount": 20,
    }


def test_aod_one_record_per_day():
    conn = GeeAodConnector(stats_fn=_canned_stats)
    envelopes = conn.ingest(
        aoi_id="AOI-DESERT", sensor="MODIS",
        datetime_range="2024-06-01T00:00:00Z/2024-06-02T23:59:59Z",
    )
    assert len(envelopes) == 2
    assert envelopes[0]._source == "MODIS_AOD"
    assert envelopes[0]._event_ts == "2024-06-01T00:00:00Z"


def test_aod_stamps_product_sensor_collection():
    conn = GeeAodConnector(stats_fn=_canned_stats)
    rec = conn.ingest(
        aoi_id="AOI-DESERT", sensor="modis",
        datetime_range="2024-06-01T00:00:00Z/2024-06-01T23:59:59Z",
    )[0].payload
    assert rec["product"] == "AOD"
    assert rec["sensor"] == "MODIS"
    assert rec["unit"] == "unitless"
    assert rec["collection"] == "MODIS/061/MCD19A2_GRANULES"
    assert rec["aoi_id"] == "AOI-DESERT"


def test_aod_bucket_shape_matches_silver_cleaner_contract():
    conn = GeeAodConnector(stats_fn=_canned_stats)
    rec = conn.ingest(
        aoi_id="AOI-UAE-NAT",
        datetime_range="2024-06-01T00:00:00Z/2024-06-01T23:59:59Z",
    )[0].payload
    stats = rec["outputs"]["index"]["bands"]["B0"]["stats"]
    assert stats["mean"] == 0.35
    assert stats["sampleCount"] == 80


def test_aod_rejects_unknown_sensor():
    conn = GeeAodConnector(stats_fn=_canned_stats)
    with pytest.raises(ValueError):
        conn.ingest(sensor="SEVIRI", aoi_id="AOI-DESERT")
