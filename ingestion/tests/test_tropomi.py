"""TROPOMI (Sentinel-5P) connector tests — mocked HttpClient, no network."""

import pytest

from ingestion.api.tropomi import TropomiConnector


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
             "min": 1e-5, "max": 5e-5, "mean": 3e-5, "stDev": 1e-5,
             "sampleCount": 90, "noDataCount": 10}}}}}}
        for f, t in intervals
    ]}


def _token():
    return {"access_token": "tok", "token_type": "bearer", "expires_in": 3600}


def test_tropomi_shapes_one_record_per_bucket():
    stats = _stats(("2024-06-01T00:00:00Z", "2024-06-02T00:00:00Z"),
                   ("2024-06-02T00:00:00Z", "2024-06-03T00:00:00Z"))
    conn = TropomiConnector(http=SequencedHttp(_token(), stats),
                            client_id="cid", client_secret="secret")
    envelopes = conn.ingest(product="NO2", aoi_id="AOI-UAE-NAT")
    assert len(envelopes) == 2
    assert envelopes[0]._source == "TROPOMI"
    assert envelopes[0]._event_ts == "2024-06-01T00:00:00Z"


def test_tropomi_stamps_product_unit_and_aoi():
    stats = _stats(("2024-06-01T00:00:00Z", "2024-06-02T00:00:00Z"))
    conn = TropomiConnector(http=SequencedHttp(_token(), stats),
                            client_id="cid", client_secret="secret")
    rec = conn.ingest(product="no2", aoi_id="AOI-UAE-NAT")[0].payload
    assert rec["product"] == "NO2"
    assert rec["unit"] == "mol/m2"
    assert rec["aoi_id"] == "AOI-UAE-NAT"
    assert rec["bbox"] == [51.0, 22.5, 56.5, 26.2]  # UAE national AOI
    assert rec["collection"] == "sentinel-5p-l2"


def test_tropomi_ch4_unit_is_ppb():
    stats = _stats(("2024-06-01T00:00:00Z", "2024-06-02T00:00:00Z"))
    conn = TropomiConnector(http=SequencedHttp(_token(), stats),
                            client_id="cid", client_secret="secret")
    rec = conn.ingest(product="CH4", aoi_id="AOI-DXB")[0].payload
    assert rec["unit"] == "ppb"


def test_tropomi_rejects_unknown_product():
    conn = TropomiConnector(http=SequencedHttp(_token()),
                            client_id="cid", client_secret="secret")
    with pytest.raises(ValueError):
        conn.ingest(product="PM25", aoi_id="AOI-DXB")


def test_tropomi_all_products_have_evalscripts():
    from ingestion.config.settings import settings
    for product in settings.climate.tropomi_products:
        assert product in TropomiConnector.EVALSCRIPTS
