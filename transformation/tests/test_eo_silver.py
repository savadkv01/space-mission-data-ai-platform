from __future__ import annotations

from transformation.batch.bronze_to_silver import (
    silver_ems_aoi,
    silver_fire,
    silver_index,
    silver_scene,
    silver_vessel,
)
from transformation.batch.silver_to_gold import gold_earth_observation


# --- Fire (FIRMS / VIIRS) ---------------------------------------------------

def test_silver_fire_conforms_and_keys(fire_records):
    result = silver_fire(fire_records)
    assert result.rows, "expected conformed fire rows"
    row = result.rows[0]
    assert row["fire_key"]
    assert row["event_ts"].endswith("+00:00")
    assert "geo_key" in row
    assert row["source"] == "VIIRS"
    assert row["confidence"] in {66, 99}


def test_silver_fire_rejects_bad_geo():
    bad = [{"latitude": 999, "longitude": 0, "acq_date": "2026-06-01",
            "acq_time": "0100", "frp": 5}]
    result = silver_fire(bad)
    assert not result.rows
    assert "range:latitude" in result.quarantine[0]["_reasons"]


def test_silver_fire_feeds_gold_earth_observation(fire_records):
    silver = silver_fire(fire_records)
    gold = gold_earth_observation(silver.rows)
    assert gold, "fire Silver rows should aggregate into EO Gold marts"
    assert all("detections" in r and "date_key" in r for r in gold)


# --- Vessel (Global Fishing Watch) ------------------------------------------

def test_silver_vessel_flattens_registry(vessel_records):
    result = silver_vessel(vessel_records)
    assert result.rows
    row = result.rows[0]
    assert row["vessel_key"] == row["mmsi"]
    assert row["flag"] == "ARE"
    assert row["shipname"].startswith("VESSEL")
    assert row["event_ts"].endswith("+00:00")


def test_silver_vessel_rejects_missing_mmsi():
    bad = [{"registryInfo": [{"shipname": "ghost",
                              "transmissionDateTo": "2026-06-01T00:00:00Z"}]}]
    result = silver_vessel(bad)
    assert not result.rows
    assert "null:mmsi" in result.quarantine[0]["_reasons"]


# --- Scene metadata (Sentinel Hub / Earthdata) ------------------------------

def test_silver_scene_extracts_metadata(scene_records):
    result = silver_scene(scene_records)
    assert result.rows
    row = result.rows[0]
    assert row["scene_key"]
    assert row["collection"] == "sentinel-2-l2a"
    assert row["geo_key"]
    assert 0 <= row["cloud_cover"] <= 100
    assert 0.0 <= row["completeness_score"] <= 1.0


def test_silver_scene_rejects_missing_id():
    bad = [{"properties": {"datetime": "2026-06-01T00:00:00Z"}}]
    result = silver_scene(bad)
    assert not result.rows
    assert "null:scene_id" in result.quarantine[0]["_reasons"]


def test_silver_scene_dedup_by_scene_key(scene_records):
    dupes = scene_records + scene_records
    result = silver_scene(dupes)
    keys = {r["scene_key"] for r in result.rows}
    assert len(keys) == len(result.rows)


def test_silver_scene_accepts_cmr_and_stac():
    """Earthdata CMR granules and LandsatLook STAC features both conform."""
    cmr = {"producer_granule_id": "G1", "time_start": "2026-06-01T00:00:00Z",
           "boxes": ["24.8 54.8 25.5 55.6"], "dataset_id": "MOD14",
           "cloud_cover": "10", "_source": "EARTHDATA"}
    stac = {"id": "LC08_X", "collection": "landsat-c2l2-sr",
            "bbox": [54.8, 24.8, 55.6, 25.5],
            "properties": {"datetime": "2026-06-02T07:00:00Z", "eo:cloud_cover": 5.0},
            "_source": "LANDSAT"}
    result = silver_scene([cmr, stac])
    assert len(result.rows) == 2
    by_key = {r["scene_key"]: r for r in result.rows}
    assert by_key["G1"]["collection"] == "MOD14"
    assert by_key["G1"]["geo_key"]  # bbox derived from CMR boxes
    assert by_key["G1"]["source"] == "EARTHDATA"
    assert by_key["LC08_X"]["source"] == "LANDSAT"
    assert by_key["LC08_X"]["cloud_cover"] == 5.0


# --- Spectral index statistics (Sentinel Hub Statistical API) ---------------

def _stats_bucket(day: str, mean: float, sample: int = 90, nodata: int = 10) -> dict:
    return {
        "interval": {"from": f"2026-06-{day}T00:00:00Z", "to": f"2026-06-{day}T23:59:59Z"},
        "outputs": {"index": {"bands": {"B0": {"stats": {
            "min": mean - 0.1, "max": mean + 0.1, "mean": mean,
            "stDev": 0.05, "sampleCount": sample, "noDataCount": nodata,
        }}}}},
        "index": "NDVI", "bbox": [54.8, 24.8, 55.6, 25.5],
        "collection": "sentinel-2-l2a", "_source": "SENTINELHUB_STATS",
    }


def test_silver_index_conforms_and_keys():
    result = silver_index([_stats_bucket("01", 0.42), _stats_bucket("02", 0.55)])
    assert len(result.rows) == 2
    row = result.rows[0]
    assert row["index_key"]
    assert row["index_name"] == "NDVI"
    assert row["stat_date"] in {"2026-06-01", "2026-06-02"}
    assert row["geo_key"]
    assert row["valid_pixel_fraction"] == 0.9
    assert row["source"] == "SENTINELHUB_STATS"


def test_silver_index_rejects_missing_stats():
    bad = [{"interval": {"from": "2026-06-01T00:00:00Z"}, "index": "NDVI",
            "bbox": [54.8, 24.8, 55.6, 25.5], "outputs": {}}]
    result = silver_index(bad)
    assert not result.rows
    assert "null:mean" in result.quarantine[0]["_reasons"]


def test_silver_index_dedup_by_key():
    dupes = [_stats_bucket("01", 0.42), _stats_bucket("01", 0.42)]
    result = silver_index(dupes)
    assert len(result.rows) == 1


# --- AOI reference layer (Copernicus EMS) -----------------------------------

def _ems_collection():
    return {
        "type": "FeatureCollection", "_source": "EMS",
        "_ingest_id": "i1", "_batch_id": "b1",
        "features": [
            {"type": "Feature",
             "properties": {"id": "EMSR100", "name": "Flood AOI",
                            "eventType": "Flood", "eventDate": "2026-06-10T00:00:00Z"},
             "geometry": {"type": "Polygon", "coordinates": [
                 [[54.8, 24.8], [55.6, 24.8], [55.6, 25.5], [54.8, 25.5], [54.8, 24.8]]]}},
            {"type": "Feature",
             "properties": {"id": "EMSR200", "name": "Wildfire AOI", "eventType": "Wildfire"},
             "geometry": {"type": "Polygon", "coordinates": [
                 [[10, 10], [11, 10], [11, 11], [10, 11], [10, 10]]]}},
        ],
    }


def test_silver_ems_aoi_expands_and_classifies():
    result = silver_ems_aoi([_ems_collection()])
    assert len(result.rows) == 2
    by = {r["aoi_key"]: r for r in result.rows}
    assert by["EMSR100"]["event_type"] == "flood"
    assert by["EMSR200"]["event_type"] == "fire"
    assert by["EMSR100"]["bbox"] == [54.8, 24.8, 55.6, 25.5]
    assert by["EMSR100"]["area_km2"] > 0
    assert by["EMSR100"]["source"] == "EMS"


def test_silver_ems_aoi_rejects_missing_geometry():
    bad = [{"type": "Feature", "properties": {"id": "X"}, "geometry": {}, "_source": "EMS"}]
    result = silver_ems_aoi(bad)
    assert not result.rows
    assert "null:geometry" in result.quarantine[0]["_reasons"]
