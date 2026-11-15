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
        aoi_id="AOI-AUH",
        datetime_range="2024-06-01T00:00:00Z/2024-06-01T23:59:59Z",
    )[0].payload
    stats = rec["outputs"]["index"]["bands"]["B0"]["stats"]
    assert stats["mean"] == 0.35
    assert stats["sampleCount"] == 80


def test_aod_rejects_unknown_sensor():
    conn = GeeAodConnector(stats_fn=_canned_stats)
    with pytest.raises(ValueError):
        conn.ingest(sensor="SEVIRI", aoi_id="AOI-DESERT")


def test_maiac_qa_mask_keeps_only_clear_best_quality_pixels():
    from ingestion.api.gee_aod import GeeAodConnector

    class Px:
        def __init__(self, v):
            self.v = v

        def bitwiseAnd(self, m):
            return Px(self.v & m)

        def rightShift(self, n):
            return Px(self.v >> n)

        def eq(self, x):
            return Px(int(self.v == x))

        def And(self, other):
            return Px(int(bool(self.v) and bool(other.v)))

    def ok(qa):
        return GeeAodConnector.maiac_qa_ok(None, Px(qa)).v

    assert ok(0b001) == 1                       # clear, best quality
    assert ok(0b011) == 0                       # cloudy
    assert ok(0b001 | (5 << 8)) == 0            # clear flag but "no retrieval"
    assert ok(0b001 | (2 << 13)) == 1           # dust aerosol model is still kept

    def model(qa):
        return GeeAodConnector.maiac_aerosol_model(Px(qa)).v

    assert model(0b001) == 0                    # background
    assert model(0b001 | (1 << 13)) == 1        # smoke
    assert model(0b011 | (2 << 13) | (5 << 8)) == 2   # dust, other bits ignored


def test_aod_records_carry_maiac_qa_and_aerosol_model_through_silver():
    from ingestion.api.gee_aod import GeeAodConnector
    from transformation.batch.climate_bronze_to_silver import silver_aerosol

    stats = {"mean": 0.5, "min": 0.1, "max": 0.9, "stDev": 0.1, "sampleCount": 9,
             "noDataCount": 1, "smokeFraction": 0.8, "dustFraction": 0.05}
    conn = GeeAodConnector(stats_fn=lambda **_: stats)
    records, _ = conn.fetch_raw(aoi_id="IN-THAR", datetime_range="2026-11-01/2026-11-01")
    assert records[0]["qa_mask"] == GeeAodConnector.QA_MASK
    assert records[0]["aerosol_model"] == GeeAodConnector.AEROSOL_MODEL
    row = silver_aerosol(records).rows[0]
    assert (row["smoke_fraction"], row["dust_fraction"]) == (0.8, 0.05)
