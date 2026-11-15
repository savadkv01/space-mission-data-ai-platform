from __future__ import annotations

from transformation.batch.bronze_to_silver import (
    silver_scene,
    silver_space_weather,
    silver_telemetry,
    silver_vessel,
)
from transformation.batch.silver_to_gold import (
    fire_aoi_attribution,
    gold_aoi_validation,
    gold_earth_observation,
    gold_flood_aoi,
    gold_launch_performance,
    gold_satellite_health,
    gold_scene_catalog,
    gold_space_weather_impact,
    gold_vessel_activity,
    gold_wildfire_aoi,
)


def test_fire_attribution_accounts_for_overlap_unmatched_and_invalid_date():
    rows = [
        {"fire_key": "in", "event_ts": "2026-10-31T00:00:00Z", "latitude": 25,
         "longitude": 55, "frp": 12.5, "brightness": 330.0,
         "brightness_source_field": "bright_ti4", "brightness_status": "present",
         "source": "VIIRS"},
        {"fire_key": "out", "event_ts": "2026-10-31T00:00:00Z", "latitude": 0, "longitude": 0},
        {"fire_key": "bad", "event_ts": "invalid", "latitude": 25, "longitude": 55},
    ]
    overlay = {**_FIRE_AOI, "aoi_key": "overlap", "rollup_eligible": False}
    aois = [_FIRE_AOI, overlay]
    ledger = fire_aoi_attribution(rows, aois)
    assert len(ledger) == 3
    # One reporting AOI plus the event overlay that also contains the point.
    assert ledger[0]["match_count"] == 2
    assert ledger[0]["reporting_aoi_key"] == "EMSR200"
    assert ledger[0]["aoi_keys"] == ["EMSR200", "overlap"]
    assert ledger[0]["frp"] == 12.5
    assert ledger[0]["brightness_source_field"] == "bright_ti4"
    assert ledger[0]["brightness_status"] == "present"
    assert ledger[0]["source"] == "VIIRS"
    assert ledger[1]["match_status"] == "unmatched"
    assert ledger[2]["match_status"] == "invalid_date" and ledger[2]["match_count"] == 0
    assert sum(r["detections"] for r in gold_wildfire_aoi(rows, aois)) == 2


def test_point_on_shared_partition_edge_counts_once():
    west = {"aoi_key": "A-WEST", "bbox": [0.0, 0.0, 1.0, 1.0],
            "polygons": [[[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]]}
    east = {"aoi_key": "B-EAST", "bbox": [1.0, 0.0, 2.0, 1.0],
            "polygons": [[[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]]}
    fire = [{"fire_key": "edge", "event_ts": "2026-11-01T00:00:00Z",
             "latitude": 0.5, "longitude": 1.0}]
    ledger = fire_aoi_attribution(fire, [east, west])
    assert ledger[0]["aoi_keys"] == ["A-WEST"]
    assert sum(r["detections"] for r in gold_wildfire_aoi(fire, [east, west])) == 1


def test_gold_satellite_health_grain(telemetry_records):
    silver = silver_telemetry(telemetry_records).rows
    gold = gold_satellite_health(silver)
    # one row per (sat, day)
    keys = {(r["sat_key"], r["date_key"]) for r in gold}
    assert len(keys) == len(gold)
    for r in gold:
        assert 0.0 <= r["health_score"] <= 1.0
        assert 0.0 <= r["anomaly_density"] <= 1.0


def test_gold_space_weather_impact(telemetry_records, space_weather_records):
    s_tel = silver_telemetry(telemetry_records).rows
    s_wea = silver_space_weather(space_weather_records).rows
    gold = gold_space_weather_impact(s_wea, s_tel)
    assert gold
    for r in gold:
        if r["anomaly_rate"] is not None:
            assert 0.0 <= r["anomaly_rate"] <= 1.0


def test_gold_launch_performance():
    launches = [
        {"event_ts": "2026-06-01T00:00:00+00:00", "provider": "P1", "success": True, "delay_days": 2},
        {"event_ts": "2026-06-15T00:00:00+00:00", "provider": "P1", "success": False, "delay_days": 5},
    ]
    gold = gold_launch_performance(launches)
    assert len(gold) == 1
    assert gold[0]["launches"] == 2
    assert gold[0]["success_rate"] == 0.5
    assert gold[0]["mean_delay_days"] == 3.5


def test_gold_earth_observation():
    fires = [
        {"event_ts": "2026-06-01T00:00:00+00:00", "geo_key": "10.0:20.0", "frp": 30},
        {"event_ts": "2026-06-01T01:00:00+00:00", "geo_key": "10.0:20.0", "frp": 50},
    ]
    gold = gold_earth_observation(fires)
    assert len(gold) == 1
    assert gold[0]["detections"] == 2
    assert gold[0]["max_frp"] == 50.0
    assert gold[0]["median_frp"] == 40.0


def test_fire_frp_means_are_invariant_to_storage_row_order():
    from itertools import permutations
    rows = [{"event_ts": "2026-10-31T00:00:00Z", "geo_key": "G",
             "latitude": 25, "longitude": 55, "frp": value}
            for value in [0.1, 0.2, 14.5575]]
    grids = [gold_earth_observation(list(order)) for order in permutations(rows)]
    aois = [gold_wildfire_aoi(list(order), [_FIRE_AOI]) for order in permutations(rows)]
    assert all(result == grids[0] for result in grids)
    assert all(result == aois[0] for result in aois)


def test_gold_vessel_activity_grain(vessel_records):
    silver = silver_vessel(vessel_records).rows
    gold = gold_vessel_activity(silver)
    assert gold
    keys = {(r["vessel_key"], r["date_key"]) for r in gold}
    assert len(keys) == len(gold)
    for r in gold:
        assert r["transmissions"] >= 1
        assert isinstance(r["suspicious_flag"], bool)


def test_gold_scene_catalog_is_searchable(scene_records):
    silver = silver_scene(scene_records).rows
    gold = gold_scene_catalog(silver)
    assert gold
    keys = {r["scene_key"] for r in gold}
    assert len(keys) == len(gold)  # 1 row per scene
    assert all(r["is_searchable"] for r in gold)
    assert all(0.0 <= r["completeness_score"] <= 1.0 for r in gold)


# --- Per-AOI marts (Action 3 geospatial joins) ------------------------------

_FIRE_AOI = {"aoi_key": "EMSR200", "event_type": "fire",
             "bbox": [54.8, 24.8, 55.6, 25.5],
             "polygons": [[[[54.8, 24.8], [55.6, 24.8], [55.6, 25.5],
                            [54.8, 25.5], [54.8, 24.8]]]]}
_FLOOD_AOI = {"aoi_key": "EMSR100", "event_type": "flood", "area_km2": 4200.0,
              "event_date": "2026-06-10T00:00:00Z",
              "bbox": [54.8, 24.8, 55.6, 25.5],
              "polygons": [[[[54.8, 24.8], [55.6, 24.8], [55.6, 25.5],
                             [54.8, 25.5], [54.8, 24.8]]]]}


def test_gold_wildfire_aoi_point_in_polygon():
    fires = [
        {"event_ts": "2026-06-11T00:00:00+00:00", "latitude": 25.0, "longitude": 55.0, "frp": 30},
        {"event_ts": "2026-06-11T01:00:00+00:00", "latitude": 25.1, "longitude": 55.1, "frp": 50},
        {"event_ts": "2026-06-11T02:00:00+00:00", "latitude": 10.0, "longitude": 10.0, "frp": 99},
    ]
    gold = gold_wildfire_aoi(fires, [_FIRE_AOI])
    assert len(gold) == 1  # only the two in-polygon detections attribute
    assert gold[0]["aoi_key"] == "EMSR200"
    assert gold[0]["detections"] == 2
    assert gold[0]["max_frp"] == 50.0


def test_gold_flood_aoi_decides_only_on_permanent_water_masked_ndwi():
    legacy = {"index_name": "NDWI", "event_ts": "2026-06-10T00:00:00+00:00",
              "bbox": "54.8,24.8,55.6,25.5", "mean": 0.3, "valid_pixel_fraction": 0.9}
    ndvi = {**legacy, "index_name": "NDVI", "mean": 0.6}
    gold = gold_flood_aoi([legacy, ndvi], [_FLOOD_AOI])
    assert len(gold) == 1
    assert gold[0]["aoi_key"] == "EMSR100"
    assert gold[0]["ndwi_mean"] == 0.3
    # Unmasked NDWI cannot tell sea from flood water: not evaluated, not True.
    assert gold[0]["flood_flag"] is None

    def masked(day, water):
        return {**legacy, "event_ts": f"{day}T00:00:00+00:00", "mean": -0.4,
                "water_mask": "jrc_gsw_v1_4_seasonality_ge10",
                "water_fraction": water, "permanent_water_fraction": 0.6}

    out = {r["date_key"]: r for r in gold_flood_aoi(
        [masked("2026-06-11", 0.005), masked("2026-06-12", 0.08),
         {**masked("2026-06-13", 0.5), "valid_pixel_fraction": 0.05}], [_FLOOD_AOI])}
    assert out["2026-06-11"]["flood_flag"] is False   # 0.5 % new water: dry
    assert out["2026-06-12"]["flood_flag"] is True    # 8 % new water: flood
    assert out["2026-06-12"]["permanent_water_fraction"] == 0.6
    assert out["2026-06-13"]["flood_flag"] is None    # 5 % valid pixels: too cloudy


def test_aoi_validation_corroborates_only_ems_activations():
    platform_aoi = {**_FIRE_AOI, "aoi_key": "IN-PB-HR", "is_ems_activation": False}
    wildfire = [{"aoi_key": "IN-PB-HR", "date_key": "2026-11-01", "detections": 400}]
    row = gold_aoi_validation([platform_aoi], wildfire, [])[0]
    assert (row["signal_present"], row["corroborated"]) == (True, False)


def test_persistent_heat_sources_are_excluded_from_wildfire_kpis():
    from transformation.batch.silver_to_gold import classify_heat_sources

    # A flare: same 0.01° cell on 6 days. A crop fire: a different cell each day.
    flare = [{"event_ts": f"2026-11-0{d}T22:00:00Z", "latitude": 25.20, "longitude": 55.20,
              "frp": 5.0} for d in range(1, 7)]
    crops = [{"event_ts": f"2026-11-0{d}T08:00:00Z", "latitude": 25.0 + d / 50,
              "longitude": 55.0, "frp": 9.0} for d in range(1, 7)]
    classes = classify_heat_sources(flare + crops)
    assert classes[:6] == ["persistent_industrial"] * 6
    assert classes[6:] == ["vegetation_fire"] * 6

    gold = gold_wildfire_aoi(flare + crops, [_FIRE_AOI])
    assert sum(r["detections"] for r in gold) == 6
    assert sum(r["persistent_detections"] for r in gold) == 6
    assert all(r["max_frp"] == 9.0 for r in gold if r["detections"])


def test_gold_aoi_validation_corroborates():
    wildfire = [{"aoi_key": "EMSR200", "date_key": "2026-06-11", "detections": 2}]
    flood = [{"aoi_key": "EMSR100", "date_key": "2026-06-10", "flood_flag": True}]
    gold = gold_aoi_validation([_FIRE_AOI, _FLOOD_AOI], wildfire, flood)
    by = {r["aoi_key"]: r for r in gold}
    assert by["EMSR200"]["corroborated"] is True
    assert by["EMSR100"]["corroborated"] is True
    assert by["EMSR100"]["event_type"] == "flood"


def test_gold_aoi_validation_uncorroborated_when_no_evidence():
    gold = gold_aoi_validation([_FIRE_AOI], [], [])
    assert gold[0]["corroborated"] is False
    assert gold[0]["evidence_days"] == 0


def test_fire_attribution_assigns_region_by_envelope_including_unmatched():
    from transformation.batch.gold_lakehouse import load_aoi_reference
    from transformation.batch.silver_to_gold import fire_aoi_attribution

    aois = load_aoi_reference()
    fires = [
        {"fire_key": "pb", "event_ts": "2026-11-01T08:00:00Z", "latitude": 30.5, "longitude": 75.5},
        {"fire_key": "in-gap", "event_ts": "2026-11-01T08:00:00Z", "latitude": 22.0, "longitude": 80.0},
        {"fire_key": "uae", "event_ts": "2026-11-01T08:00:00Z", "latitude": 25.0, "longitude": 55.2},
        {"fire_key": "africa", "event_ts": "2026-11-01T08:00:00Z", "latitude": 5.0, "longitude": 35.0},
    ]
    out = {r["fire_key"]: r for r in fire_aoi_attribution(fires, aois)}
    assert (out["pb"]["region"], out["pb"]["aoi_keys"]) == ("INDIA", ["IN-PB-HR"])
    assert (out["in-gap"]["region"], out["in-gap"]["match_status"]) == ("INDIA", "unmatched")
    assert out["uae"]["region"] == "UAE-GULF"
    assert out["africa"]["region"] is None


def test_aoi_seed_assigns_every_footprint_a_region():
    from collections import Counter

    from transformation.batch.gold_lakehouse import load_aoi_reference

    regions = Counter(a["region"] for a in load_aoi_reference())
    assert regions == {"UAE-GULF": 11, "INDIA": 6, "US-LEGACY": 1}


def test_aoi_seed_reporting_units_partition_and_match_ingestion_boxes():
    from ingestion.config.settings import settings
    from transformation.batch.gold_lakehouse import load_aoi_reference
    from transformation.geospatial.spatial_transform import (
        overlapping_reporting_pairs,
        reporting_aois,
    )

    aois = load_aoi_reference()
    assert overlapping_reporting_pairs(aois) == []
    overlays = {a["aoi_key"] for a in aois if a["rollup_eligible"] is False}
    assert overlays == {"EMSR-AE-FLOOD-2024"}
    # Request boxes must equal the seed geometry, or Silver quarantines the
    # records as superseded (ADR-12).
    seed = {a["aoi_key"]: a["bbox"] for a in reporting_aois(aois)
            if a["aoi_key"] in settings.climate.aois}
    assert set(seed) == set(settings.climate.aois)
    assert all(seed[k] == list(v) for k, v in settings.climate.aois.items())


def _maritime(dataset, aoi, day, flag, value, vessels, ingest="2026-11-14T00:00:00Z"):
    measure = {"detections": value} if dataset == "sar" else {"hours": value}
    return {"dataset": dataset, "aoi_id": aoi, "date": day, "flag": flag,
            "vessel_count": vessels, "_ingest_ts": ingest, **measure}


def test_silver_maritime_latest_pull_wins_and_flags_unmatched():
    from transformation.batch.bronze_to_silver import silver_maritime_activity

    result = silver_maritime_activity([
        _maritime("presence", "AOI-GULF", "2026-11-01", "SAU", 10.0, 2, "2026-11-13T00:00:00Z"),
        _maritime("presence", "AOI-GULF", "2026-11-01", "SAU", 12.0, 3, "2026-11-14T00:00:00Z"),
        _maritime("sar", "AOI-GULF", "2026-11-01", None, 7, 1),
        _maritime("tracks", "AOI-GULF", "2026-11-01", "SAU", 1.0, 1),
    ])
    rows = {(r["dataset"], r["flag"]): r for r in result.rows}
    assert rows[("presence", "SAU")]["hours"] == 12.0
    assert rows[("sar", None)]["ais_matched"] is False
    assert result.quarantine[0]["_reasons"] == ["unknown:dataset"]


def test_gold_maritime_zero_only_where_published_else_not_published():
    from transformation.batch.bronze_to_silver import silver_maritime_activity
    from transformation.batch.silver_to_gold import gold_maritime_activity

    silver = silver_maritime_activity([
        _maritime("presence", "AOI-GULF", "2026-11-01", "SAU", 10.0, 2),
        _maritime("presence", "AOI-GULF", "2026-11-03", "SAU", 8.0, 1),
        _maritime("fishing_effort", "AOI-GULF", "2026-11-01", "IRN", 5.0, 1),
        _maritime("sar", "AOI-GULF", "2026-11-01", None, 6, 2),
        _maritime("sar", "AOI-GULF", "2026-11-01", "SAU", 2, 2),
    ]).rows
    rows = {r["date_key"]: r for r in gold_maritime_activity(silver)}

    assert sorted(rows) == ["2026-11-01", "2026-11-02", "2026-11-03"]
    d1, d2, d3 = rows["2026-11-01"], rows["2026-11-02"], rows["2026-11-03"]
    assert (d1["sar_detections"], d1["sar_unmatched_detections"], d1["sar_dark_fraction"]) == (8, 6, 0.75)
    assert (d2["presence_hours"], d2["presence_status"]) == (0.0, "measured")
    assert (d3["fishing_hours"], d3["fishing_status"]) == (None, "not_published")
    assert (d3["sar_detections"], d3["sar_status"]) == (None, "not_published")


def test_gold_maritime_marks_trailing_days_provisional():
    from transformation.batch.bronze_to_silver import silver_maritime_activity
    from transformation.batch.silver_to_gold import gold_maritime_activity

    silver = silver_maritime_activity([
        _maritime("presence", "AOI-GULF", f"2026-11-{d:02d}", "SAU", 10.0, 2)
        for d in range(1, 11)
    ]).rows
    rows = {r["date_key"]: r["is_provisional"] for r in gold_maritime_activity(silver)}
    assert rows["2026-11-05"] is False
    assert [d for d, p in sorted(rows.items()) if p] == [
        "2026-11-06", "2026-11-07", "2026-11-08", "2026-11-09", "2026-11-10"]


def test_silver_maritime_quarantines_superseded_aoi_geometry():
    from transformation.batch.bronze_to_silver import silver_maritime_activity

    seed = [{"aoi_key": "AOI-GULF", "bbox": [48.0, 26.2, 57.0, 30.5]}]
    old = {**_maritime("presence", "AOI-GULF", "2026-11-01", "SAU", 10.0, 2),
           "bbox": [48.0, 24.0, 57.0, 30.5]}
    new = {**_maritime("presence", "AOI-GULF", "2026-11-02", "SAU", 9.0, 2),
           "bbox": [48.0, 26.2, 57.0, 30.5]}
    retired = {**_maritime("presence", "AOI-UAE-NAT", "2026-11-01", "SAU", 1.0, 1),
               "bbox": [51.0, 22.5, 56.5, 26.2]}
    result = silver_maritime_activity([old, new, retired], seed)
    assert [r["stat_date"] for r in result.rows] == ["2026-11-02"]
    assert sorted(q["_reasons"][0] for q in result.quarantine) == [
        "retired:aoi", "superseded:aoi_geometry"]
