import pytest

from ingestion.api.gfw_4wings import GFW_DATASETS, GfwAreaConnector


class PostHttp:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def post_json(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.payload


def test_area_report_is_spatially_aggregated_and_flattened():
    payload = {"entries": [{"public-global-sar-presence:v5.0": [
        {"date": "2026-11-05", "flag": "", "detections": 12, "vesselIDs": 3},
        {"date": "2026-11-05", "flag": "IND", "detections": 4, "vesselIDs": 4},
    ]}]}
    http = PostHttp(payload)
    conn = GfwAreaConnector(http=http, token="t")
    records, _ = conn.fetch_raw(aoi_id="IN-MUM", dataset="sar",
                                date_from="2026-11-01", date_to="2026-11-05")

    url, kwargs = http.calls[0]
    assert "spatial-aggregation=true" in url and "group-by=FLAG" in url
    assert GFW_DATASETS["sar"].replace(":", "%3A") in url
    assert kwargs["headers"]["Authorization"] == "Bearer t"
    assert kwargs["json"]["geojson"]["coordinates"][0][0] == [72.75, 18.85]
    assert [(r["flag"], r["detections"], r["vessel_count"]) for r in records] == [
        (None, 12, 3), ("IND", 4, 4)]
    assert conn._event_ts(records[0]) == "2026-11-05T00:00:00Z"


def test_unknown_dataset_and_missing_token_fail_loudly():
    with pytest.raises(ValueError):
        GfwAreaConnector(http=PostHttp({}), token="t").fetch_raw(
            aoi_id="IN-MUM", dataset="tracks", date_from="2026-11-01", date_to="2026-11-02")
    conn = GfwAreaConnector(http=PostHttp({}), token="t")
    conn.token = ""
    with pytest.raises(RuntimeError, match="GFW_API_TOKEN"):
        conn.fetch_raw(aoi_id="IN-MUM", dataset="sar", date_from="2026-11-01", date_to="2026-11-02")