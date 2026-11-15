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
        self.calls = []

    def get(self, url, **kwargs):
        return FakeResponse(json_data=self._json, text=self._text)

    def get_json(self, url, **kwargs):
        self.calls.append((url, kwargs))
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
    envelopes = conn.ingest(latitude=25.2, longitude=55.27, aoi_id="AOI-DXB")
    assert len(envelopes) == 2
    assert envelopes[0]._source == "POWER"
    assert envelopes[0].payload["parameter"] == "T2M"
    assert envelopes[0].payload["aoi_id"] == "AOI-DXB"
    assert envelopes[0]._event_ts == "2024-01-01T00:00:00Z"
    assert "WD2M" in conn.http.calls[0][1]["params"]["parameters"]


def test_swpc_connector_normalizes_current_object_response():
    payload = [
        {"time_tag": "2024-01-01T00:00:00", "Kp": 3.0, "station_count": 8},
        {"time_tag": "2024-01-01T03:00:00", "Kp": 4.0, "station_count": 8},
    ]
    conn = SwpcConnector(http=FakeHttp(json_data=payload))
    envelopes = conn.ingest()
    assert len(envelopes) == 2
    assert envelopes[0].payload["time_tag"] == "2024-01-01T00:00:00"
    assert envelopes[0].payload["kp_index"] == 3.0
    assert envelopes[0].payload["station_count"] == 8
    assert envelopes[0]._event_ts == "2024-01-01T00:00:00Z"


def test_swpc_connector_keeps_legacy_header_response_compatibility():
    payload = [["time_tag", "kp"], ["2024-01-01 00:00:00", "3"]]
    envelopes = SwpcConnector(http=FakeHttp(json_data=payload)).ingest()
    assert envelopes[0].payload["kp_index"] == "3"
    assert envelopes[0]._event_ts == "2024-01-01T00:00:00Z"


def test_gfw_connector_extracts_entries():
    payload = {"total": 2, "entries": [{"id": "a"}, {"id": "b"}]}
    conn = GfwConnector(http=FakeHttp(json_data=payload), token="fake-token")
    envelopes = conn.ingest(query="Maria", limit=2)
    assert len(envelopes) == 2
    assert envelopes[0]._source == "GFW"
    assert envelopes[0].payload == {"id": "a"}


def test_gfw_event_time_uses_latest_transmission_date():
    record = {
        "registryInfo": [{
            "transmissionDateFrom": "2021-01-01T00:00:00Z",
            "transmissionDateTo": "2026-10-30T00:00:00Z",
        }]
    }
    envelope = GfwConnector(http=FakeHttp(json_data={"entries": [record]}),
                            token="fake-token").ingest()[0]
    assert envelope._event_ts == "2026-10-30T00:00:00Z"


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


def test_firms_header_only_csv_is_a_genuine_zero_detection_response():
    from ingestion.api.nasa_firms import FirmsConnector

    conn = FirmsConnector(http=FakeHttp(text="latitude,longitude,acq_date,acq_time\n"), map_key="k")
    assert conn.ingest() == []


def test_firms_non_csv_body_fails_instead_of_reading_as_no_fires():
    import pytest

    from ingestion.api.nasa_firms import FirmsConnector

    conn = FirmsConnector(http=FakeHttp(text="Invalid MAP_KEY."), map_key="k")
    with pytest.raises(RuntimeError, match="non-CSV response"):
        conn.ingest()


def test_firms_backfill_date_and_cap_are_reported_as_capped_coverage():
    from ingestion.api.nasa_firms import FirmsConnector
    from ingestion.batch.ingest_task import run_connector_to_bronze

    csv = "latitude,longitude,acq_date,acq_time\n" + "\n".join(
        f"30.1,75.2,2026-10-2{d},0{h}00" for d in range(1, 4) for h in range(1, 3))
    http = FakeHttp(text=csv)
    calls = []
    http.get = lambda url, **kw: (calls.append(url), FakeResponse(text=csv))[1]

    class NullWriter:
        def write_batch(self, *_args):
            return "key"

    result = run_connector_to_bronze(FirmsConnector(http=http, map_key="k"), writer=NullWriter(),
                                     area="73.8,29.0,77.4,32.5", days=5, date="2026-10-21",
                                     max_records=4)
    assert calls[0].endswith("/73.8,29.0,77.4,32.5/5/2026-10-21")
    assert result["records"] == 4 and result["coverage"] == "capped"
    assert "kept 4 most recent of 6" in result["coverage_notes"][0]


def test_firms_rejects_day_range_above_api_limit():
    import pytest

    from ingestion.api.nasa_firms import FirmsConnector

    with pytest.raises(ValueError, match="1..5"):
        FirmsConnector(http=FakeHttp(text=""), map_key="k").fetch_raw(days=6)


def test_power_requests_utc_days_and_stamps_time_standard():
    payload = {"properties": {"parameter": {"WS2M": {"20261101": 4.0}}}}
    http = FakeHttp(json_data=payload)
    records, _ = PowerConnector(http=http).fetch_raw(aoi_id="AOI-DXB")
    assert http.calls[0][1]["params"]["time-standard"] == "UTC"
    assert records[0]["time_standard"] == "UTC"
