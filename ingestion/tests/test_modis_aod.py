"""MODIS/VIIRS AOD connector tests — mocked HttpClient, no network."""

import pytest

from ingestion.api.modis_aod import ModisAodConnector


class SequencedHttp:
    """Returns queued JSON payloads in order for post_json/get_json calls."""

    def __init__(self, *payloads):
        self._payloads = list(payloads)

    def post_json(self, url, **kwargs):
        return self._payloads.pop(0)

    def get_json(self, url, **kwargs):
        return self._payloads.pop(0)


def _stats(*intervals):
    return {"data": [
        {"interval": {"from": f, "to": t},
         "outputs": {"index": {"bands": {"B0": {"stats": {
             "min": 0.1, "max": 1.2, "mean": 0.6, "stDev": 0.3,
             "sampleCount": 70, "noDataCount": 30}}}}}}
        for f, t in intervals
    ]}


def _token():
    return {"access_token": "tok", "token_type": "bearer", "expires_in": 3600}


def test_modis_aod_shapes_one_record_per_bucket():
    stats = _stats(("2024-06-01T00:00:00Z", "2024-06-02T00:00:00Z"),
                   ("2024-06-02T00:00:00Z", "2024-06-03T00:00:00Z"))
    conn = ModisAodConnector(http=SequencedHttp(_token(), stats),
                             client_id="cid", client_secret="secret")
    envelopes = conn.ingest(aoi_id="AOI-DESERT", sensor="MODIS")
    assert len(envelopes) == 2
    assert envelopes[0]._source == "MODIS_AOD"
    assert envelopes[0]._event_ts == "2024-06-01T00:00:00Z"


def test_modis_aod_stamps_sensor_product_and_aoi():
    stats = _stats(("2024-06-01T00:00:00Z", "2024-06-02T00:00:00Z"))
    conn = ModisAodConnector(http=SequencedHttp(_token(), stats),
                             client_id="cid", client_secret="secret")
    rec = conn.ingest(aoi_id="AOI-ARABIA", sensor="viirs")[0].payload
    assert rec["product"] == "AOD"
    assert rec["sensor"] == "VIIRS"
    assert rec["unit"] == "unitless"
    assert rec["aoi_id"] == "AOI-ARABIA"
    assert rec["bbox"] == [42.0, 18.0, 55.0, 30.0]  # Arabian Peninsula AOI


def test_modis_aod_rejects_unknown_sensor():
    conn = ModisAodConnector(http=SequencedHttp(_token()),
                             client_id="cid", client_secret="secret")
    with pytest.raises(ValueError):
        conn.ingest(aoi_id="AOI-DESERT", sensor="SEVIRI")


def test_modis_aod_bucket_carries_retrieval_counts():
    stats = _stats(("2024-06-01T00:00:00Z", "2024-06-02T00:00:00Z"))
    conn = ModisAodConnector(http=SequencedHttp(_token(), stats),
                             client_id="cid", client_secret="secret")
    rec = conn.ingest(aoi_id="AOI-DESERT")[0].payload
    band_stats = rec["outputs"]["index"]["bands"]["B0"]["stats"]
    # Retrieval completeness (valid vs no-data) is preserved for Silver QA.
    assert band_stats["sampleCount"] == 70
    assert band_stats["noDataCount"] == 30
