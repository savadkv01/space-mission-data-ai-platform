"""GEE Sentinel-5P (TROPOMI) connector tests — injected stats_fn, no GEE SDK."""

import pytest

from ingestion.api.gee_s5p import GeeS5pConnector


def _canned_stats(**kwargs):
    """Return one day's SH-stats-compatible statistics block."""
    return {
        "mean": 3e-5, "min": 1e-5, "max": 5e-5, "stDev": 1e-5,
        "sampleCount": 90, "noDataCount": 10,
    }


def _empty_stats(**kwargs):
    return None


def test_s5p_one_record_per_day():
    conn = GeeS5pConnector(stats_fn=_canned_stats)
    envelopes = conn.ingest(
        product="NO2", aoi_id="AOI-UAE-NAT",
        datetime_range="2024-06-01T00:00:00Z/2024-06-03T23:59:59Z",
    )
    assert len(envelopes) == 3  # 3 inclusive days
    assert envelopes[0]._source == "TROPOMI"
    assert envelopes[0]._event_ts == "2024-06-01T00:00:00Z"


def test_s5p_stamps_product_unit_collection_aoi():
    conn = GeeS5pConnector(stats_fn=_canned_stats)
    rec = conn.ingest(
        product="no2", aoi_id="AOI-UAE-NAT",
        datetime_range="2024-06-01T00:00:00Z/2024-06-01T23:59:59Z",
    )[0].payload
    assert rec["product"] == "NO2"
    assert rec["unit"] == "mol/m2"
    assert rec["aoi_id"] == "AOI-UAE-NAT"
    assert rec["bbox"] == [51.0, 22.5, 56.5, 26.2]  # UAE national AOI
    assert rec["collection"] == "COPERNICUS/S5P/OFFL/L3_NO2"


def test_s5p_bucket_shape_matches_silver_cleaner_contract():
    conn = GeeS5pConnector(stats_fn=_canned_stats)
    rec = conn.ingest(
        product="NO2", aoi_id="AOI-DXB",
        datetime_range="2024-06-01T00:00:00Z/2024-06-01T23:59:59Z",
    )[0].payload
    stats = rec["outputs"]["index"]["bands"]["B0"]["stats"]
    assert stats["mean"] == 3e-5
    assert rec["interval"]["from"] == "2024-06-01T00:00:00Z"


def test_s5p_ch4_unit_is_ppb():
    conn = GeeS5pConnector(stats_fn=_canned_stats)
    rec = conn.ingest(
        product="CH4", aoi_id="AOI-DXB",
        datetime_range="2024-06-01T00:00:00Z/2024-06-01T23:59:59Z",
    )[0].payload
    assert rec["unit"] == "ppb"
    assert rec["collection"] == "COPERNICUS/S5P/OFFL/L3_CH4"


def test_s5p_skips_days_without_imagery():
    conn = GeeS5pConnector(stats_fn=_empty_stats)
    envelopes = conn.ingest(
        product="NO2", aoi_id="AOI-DXB",
        datetime_range="2024-06-01T00:00:00Z/2024-06-05T23:59:59Z",
    )
    assert envelopes == []


def test_s5p_rejects_unknown_product():
    conn = GeeS5pConnector(stats_fn=_canned_stats)
    with pytest.raises(ValueError):
        conn.ingest(product="PM25", aoi_id="AOI-DXB")


def test_s5p_all_configured_products_have_collections():
    from ingestion.config.settings import settings
    for product in settings.climate.tropomi_products:
        assert product in GeeS5pConnector.PRODUCTS
