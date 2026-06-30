"""Connector tests using a fake HttpClient — no network calls."""

from ingestion.api.nasa_power import PowerConnector
from ingestion.api.noaa_swpc import SwpcConnector


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
