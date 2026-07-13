"""OpenAQ connector tests — mocked HttpClient, no network.

OpenAQ v3 has no flat bbox measurements endpoint; the connector makes one
``/v3/locations`` call (stations + their sensors) followed by one
``/v3/sensors/{id}/measurements`` call per matching sensor.
"""

from ingestion.api.openaq import OpenAqConnector


class SequencedHttp:
    """Returns queued JSON payloads in order (locations call, then per-sensor calls)."""

    def __init__(self, *payloads):
        self._payloads = list(payloads)

    def get_json(self, url, **kwargs):
        return self._payloads.pop(0) if self._payloads else {"results": []}


def _location(loc_id, name, sensors, lat=25.1, lon=55.2):
    return {
        "id": loc_id, "name": name,
        "coordinates": {"latitude": lat, "longitude": lon},
        "sensors": sensors,
    }


def _sensor(sensor_id, param_name):
    return {"id": sensor_id, "parameter": {"name": param_name}}


def _measurement(value, ts, param_name="pm25", units="µg/m³"):
    return {
        "value": value,
        "parameter": {"name": param_name, "units": units},
        "period": {"datetimeFrom": {"utc": ts}},
        "coordinates": None,
    }


def test_openaq_shapes_one_record_per_measurement():
    locations = {"results": [
        _location(1, "Dubai-1", [_sensor(10, "pm25"), _sensor(11, "no2")]),
    ]}
    pm25 = {"results": [_measurement(12.0, "2024-06-01T00:00:00Z", "pm25")]}
    no2 = {"results": [_measurement(20.0, "2024-06-01T00:00:00Z", "no2")]}
    conn = OpenAqConnector(http=SequencedHttp(locations, pm25, no2), api_key="k")
    envelopes = conn.ingest(aoi_id="AOI-DXB", pollutants=["pm25", "no2"], limit=1000)
    assert len(envelopes) == 2
    assert envelopes[0]._source == "OPENAQ"
    assert envelopes[0].payload["parameter"]["name"] == "pm25"
    assert envelopes[0]._event_ts == "2024-06-01T00:00:00Z"


def test_openaq_stamps_aoi_and_bbox_context():
    locations = {"results": [_location(1, "Dubai-1", [_sensor(10, "o3")])]}
    measurements = {"results": [_measurement(30.0, "2024-06-02T00:00:00Z", "o3")]}
    conn = OpenAqConnector(http=SequencedHttp(locations, measurements), api_key="k")
    envelopes = conn.ingest(aoi_id="AOI-DXB", pollutants=["o3"], limit=1000)
    rec = envelopes[0].payload
    assert rec["aoi_id"] == "AOI-DXB"
    assert rec["bbox"] == [54.9, 24.8, 55.6, 25.4]  # Dubai AOI from settings
    assert rec["locationId"] == 1
    assert rec["sensorsId"] == 10


def test_openaq_custom_bbox_overrides_aoi_lookup():
    locations = {"results": [_location(1, "Dubai-1", [_sensor(10, "co")])]}
    measurements = {"results": [_measurement(0.4, "2024-06-03T00:00:00Z", "co")]}
    conn = OpenAqConnector(http=SequencedHttp(locations, measurements), api_key="k")
    envelopes = conn.ingest(bbox=[10.0, 10.0, 11.0, 11.0], pollutants=["co"], limit=1000)
    assert envelopes[0].payload["bbox"] == [10.0, 10.0, 11.0, 11.0]


def test_openaq_skips_sensors_outside_requested_pollutants():
    locations = {"results": [_location(1, "Dubai-1", [_sensor(10, "temperature")])]}
    conn = OpenAqConnector(http=SequencedHttp(locations), api_key="k")
    envelopes = conn.ingest(aoi_id="AOI-DXB", pollutants=["pm25"])
    assert envelopes == []


def test_openaq_falls_back_to_station_coordinates_when_measurement_lacks_them():
    locations = {"results": [_location(1, "Dubai-1", [_sensor(10, "pm10")], lat=25.5, lon=55.5)]}
    measurements = {"results": [_measurement(40.0, "2024-06-01T00:00:00Z", "pm10")]}
    conn = OpenAqConnector(http=SequencedHttp(locations, measurements), api_key="k")
    envelopes = conn.ingest(aoi_id="AOI-DXB", pollutants=["pm10"])
    coords = envelopes[0].payload["coordinates"]
    assert coords == {"latitude": 25.5, "longitude": 55.5}


def test_openaq_empty_locations_returns_no_records():
    conn = OpenAqConnector(http=SequencedHttp({"results": []}), api_key="k")
    envelopes = conn.ingest(aoi_id="AOI-DXB")
    assert envelopes == []
