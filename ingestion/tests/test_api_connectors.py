"""Connector tests using a fake HttpClient — no network calls."""

from ingestion.api.earthdata import EarthdataConnector
from ingestion.api.gfw import GfwConnector
from ingestion.api.landsat import LandsatConnector
from ingestion.api.nasa_power import PowerConnector
from ingestion.api.noaa_swpc import SwpcConnector
from ingestion.api.sentinelhub import SentinelHubConnector
from ingestion.api.sentinelhub_stats import SentinelHubStatsConnector


class FakeResponse:
    def __init__(self, *, json_data=None, text=""):
        self._json = json_data
        self.text = text

    def json(self):
        return self._json

    def raise_for_status(self):
        return None


class FakeHttp:
    def __init__(self, *, json_data=None, text=""):
        self._json = json_data
        self._text = text

    def get(self, url, **kwargs):
        return FakeResponse(json_data=self._json, text=self._text)

    def get_json(self, url, **kwargs):
        return self._json


class SequencedHttp:
    """Returns queued JSON payloads in order for post_json/get_json calls."""

    def __init__(self, *payloads):
        self._payloads = list(payloads)

    def _next(self):
        return self._payloads.pop(0)

    def post_json(self, url, **kwargs):
        return self._next()

    def get_json(self, url, **kwargs):
        return self._next()



def test_power_connector_flattens_records():
    payload = {"properties": {"parameter": {"T2M": {"20240101": 20.0, "20240102": 21.0}}}}
    conn = PowerConnector(http=FakeHttp(json_data=payload))
    envelopes = conn.ingest(latitude=25.2, longitude=55.27)
    assert len(envelopes) == 2
    assert envelopes[0]._source == "POWER"
    assert envelopes[0].payload["parameter"] == "T2M"
    assert envelopes[0]._event_ts == "2024-01-01T00:00:00Z"


def test_swpc_connector_zips_header():
    payload = [["time_tag", "kp"], ["2024-01-01 00:00:00", "3"], ["2024-01-01 03:00:00", "4"]]
    conn = SwpcConnector(http=FakeHttp(json_data=payload))
    envelopes = conn.ingest()
    assert len(envelopes) == 2
    assert envelopes[0].payload == {"time_tag": "2024-01-01 00:00:00", "kp": "3"}
    assert envelopes[0]._event_ts == "2024-01-01T00:00:00Z"


def test_gfw_connector_extracts_entries():
    payload = {"total": 2, "entries": [{"id": "a"}, {"id": "b"}]}
    conn = GfwConnector(http=FakeHttp(json_data=payload), token="fake-token")
    envelopes = conn.ingest(query="Maria", limit=2)
    assert len(envelopes) == 2
    assert envelopes[0]._source == "GFW"
    assert envelopes[0].payload == {"id": "a"}


def test_gfw_connector_requires_token():
    conn = GfwConnector(http=FakeHttp(json_data={}), token="placeholder")
    conn.token = ""  # force-empty to exercise the guard regardless of env config
    try:
        conn.ingest()
    except RuntimeError as exc:
        assert "GFW_API_TOKEN" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected RuntimeError for missing token")


def test_sentinelhub_connector_parses_features():
    token = {"access_token": "tok", "token_type": "bearer", "expires_in": 3600}
    catalog = {"features": [
        {"id": "S2A_1", "properties": {"datetime": "2024-01-05T07:00:00Z"}},
        {"id": "S2A_2", "properties": {"datetime": "2024-01-10T07:00:00Z"}},
    ]}
    conn = SentinelHubConnector(http=SequencedHttp(token, catalog),
                                client_id="cid", client_secret="secret")
    envelopes = conn.ingest(collection="sentinel-2-l2a")
    assert len(envelopes) == 2
    assert envelopes[0]._source == "SENTINELHUB"
    assert envelopes[0]._event_ts == "2024-01-05T07:00:00Z"


def test_sentinelhub_stats_connector_parses_intervals():
    token = {"access_token": "tok", "token_type": "bearer", "expires_in": 3600}
    stats = {"data": [
        {"interval": {"from": "2024-06-01T00:00:00Z", "to": "2024-06-02T00:00:00Z"},
         "outputs": {"index": {"bands": {"B0": {"stats": {
             "min": 0.3, "max": 0.7, "mean": 0.5, "stDev": 0.1,
             "sampleCount": 90, "noDataCount": 10}}}}}},
        {"interval": {"from": "2024-06-02T00:00:00Z", "to": "2024-06-03T00:00:00Z"},
         "outputs": {"index": {"bands": {"B0": {"stats": {
             "min": 0.4, "max": 0.8, "mean": 0.6, "stDev": 0.1,
             "sampleCount": 80, "noDataCount": 20}}}}}},
    ]}
    conn = SentinelHubStatsConnector(http=SequencedHttp(token, stats),
                                     client_id="cid", client_secret="secret")
    envelopes = conn.ingest(index="NDVI")
    assert len(envelopes) == 2
    assert envelopes[0]._source == "SENTINELHUB_STATS"
    assert envelopes[0]._event_ts == "2024-06-01T00:00:00Z"
    assert envelopes[0].payload["index"] == "NDVI"
    assert envelopes[0].payload["bbox"] == [54.8, 24.8, 55.6, 25.5]


def test_earthdata_connector_extracts_granules():
    payload = {"feed": {"entry": [
        {"producer_granule_id": "G1", "time_start": "2024-01-01T00:00:00Z",
         "boxes": ["24.8 54.8 25.5 55.6"], "dataset_id": "MOD14", "cloud_cover": "10"},
        {"producer_granule_id": "G2", "time_start": "2024-01-02T00:00:00Z",
         "dataset_id": "MOD14"},
    ]}}
    conn = EarthdataConnector(http=FakeHttp(json_data=payload))
    envelopes = conn.ingest(short_name="MOD14")
    assert len(envelopes) == 2
    assert envelopes[0]._source == "EARTHDATA"
    assert envelopes[0]._event_ts == "2024-01-01T00:00:00Z"
    assert envelopes[0].payload["producer_granule_id"] == "G1"


def test_landsat_connector_parses_features():
    payload = {"features": [
        {"id": "LC08_X", "collection": "landsat-c2l2-sr", "bbox": [54.8, 24.8, 55.6, 25.5],
         "properties": {"datetime": "2024-01-01T07:00:00Z", "eo:cloud_cover": 5.0}},
    ]}
    conn = LandsatConnector(http=SequencedHttp(payload))
    envelopes = conn.ingest()
    assert len(envelopes) == 1
    assert envelopes[0]._source == "LANDSAT"
    assert envelopes[0]._event_ts == "2024-01-01T07:00:00Z"

