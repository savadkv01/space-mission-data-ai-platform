from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from transformation.batch.bronze_to_silver import silver_fire
from transformation.batch.gold_lakehouse import build_marts
from transformation.readiness import (
    CATALOG_PATHS, GOLD_PATHS, DatasetProfile, catalog_entries, fire_readiness,
    source_inventory,
)
from serving.marts.serving_marts import serve_wildfire_daily
from transformation.scripts.readiness_snapshot import json_records, serving_evidence

NOW = datetime(2026, 10, 31, 12, tzinfo=timezone.utc)
AOI = {"aoi_key": "A", "bbox": [0, 0, 2, 2],
       "polygons": [[[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]]}


def records():
    return [{
        "_source": "FIRMS", "_ingest_id": str(i), "_batch_id": "batch",
        "_ingest_ts": "2026-10-31T11:30:00Z",
        "payload": {"latitude": lat, "longitude": lon, "satellite": "N",
                    "instrument": "VIIRS", "acq_date": "2026-10-31", "acq_time": "1100",
                    "bright_ti4": "330.2", "bright_ti5": "290.1",
                    "frp": "12.5", "confidence": "n"},
    } for i, (lat, lon) in enumerate([(1, 1), (3, 3)])]


def test_catalog_covers_exactly_all_documented_sources():
    path = Path(__file__).resolve().parents[2] / "docs" / "source-data-analysis" / "01-dataset-inventory.md"
    entries = catalog_entries(path.read_text(encoding="utf-8"))
    assert len(entries) == 45
    assert CATALOG_PATHS[35][2] == ["silver_wind"]
    assert "fact_dust_event_daily" in GOLD_PATHS["silver_wind"]
    inventory = source_inventory(entries, {}, set(), NOW)
    assert len(inventory) == 45
    assert all(not row["analysis_ready"] and row["refreshable"] is None for row in inventory)
    with pytest.raises(ValueError, match="unique entries"):
        catalog_entries("| 1 | Only one source |")


def test_json_parser_supports_existing_ndjson_fixture_extensions():
    assert list(json_records('{"a": 1}\n{"a": 2}\n')) == [{"a": 1}, {"a": 2}]
    assert list(json_records('[{"a": 1}, {"a": 2}]')) == [{"a": 1}, {"a": 2}]
    assert list(json_records('{\n"a": 1\n}')) == [{"a": 1}]
    with pytest.raises(ValueError):
        list(json_records('[1]'))
    with pytest.raises(ValueError):
        list(json_records('{"a": 1}\nmalformed'))


def test_serving_snapshot_qualifies_ambiguous_catalog_and_schema(tmp_path):
    duckdb = pytest.importorskip("duckdb")
    path = tmp_path / "serving.duckdb"
    with duckdb.connect(str(path)) as connection:
        connection.execute("CREATE SCHEMA serving")
        connection.execute('CREATE TABLE serving.serving.serving_wildfire_daily '
                           '(aoi_key VARCHAR, date_key VARCHAR, detections INTEGER)')
        connection.execute("INSERT INTO serving.serving.serving_wildfire_daily "
                           "VALUES ('A', '2026-10-31', 1)")
    summaries, rows = serving_evidence(path, NOW)
    assert summaries[0]["row_count"] == 1
    assert summaries[0]["event_time_max"] == "2026-10-31T00:00:00+00:00"
    assert rows[0]["detections"] == 1


def test_profile_reports_unknown_invalid_and_fresh_times_separately():
    profile = DatasetProfile("s3://bronze/FIRMS")
    profile.add({"_event_ts": "2026-10-31T11:00:00Z", "_ingest_ts": "2026-10-31T11:30:00Z",
                 "payload": {"frp": 1}})
    profile.add({"_event_ts": "invalid", "payload": {"frp": None}})
    profile.add({"payload": {"frp": None}})
    report = profile.report(NOW)
    assert report["row_count"] == 3
    assert report["freshness_hours"] == 1
    assert report["invalid_event_times"] == report["missing_event_times"] == 1
    assert len(report["observed_field_schema_versions"]) == 1
    source = source_inventory([{"catalog_id": 9}], {profile.path: profile},
                              {"ingestion/api/nasa_firms.py"}, NOW)[0]
    assert source["populated"] and source["implemented"] and source["refreshable"]
    assert source["source_access_status"] == "recent_landing_evidence"
    assert not source["analysis_ready"]


def test_fire_contract_reconciles_duplicates_and_all_detections():
    from transformation.common.io import unwrap_bronze
    bronze = records()
    bronze.append(bronze[0])
    silver = silver_fire([unwrap_bronze(r) for r in bronze]).rows
    marts = build_marts({"fire": silver}, [AOI])
    serving = serve_wildfire_daily(marts["kpi_wildfire_aoi_daily"])
    report = fire_readiness(bronze, silver, marts, [AOI], NOW, serving)
    assert report["technical_status"] == "pass"
    assert report["quality_status"] == "blocked"
    assert report["counts"]["duplicates_removed"] == 1
    assert report["counts"]["matched"] == report["counts"]["unmatched"] == 1
    assert report["counts"]["aoi_assignments"] == report["counts"]["gold_detections"] == 1
    assert report["key_field_completeness"]["brightness"]["missing_count"] == 0


@pytest.mark.parametrize("defect", ["mapping", "ledger", "gold", "serving", "stale"])
def test_contract_blocks_mapping_loss_missing_evidence_and_staleness(defect):
    from transformation.common.io import unwrap_bronze
    bronze = records()
    silver = silver_fire([unwrap_bronze(r) for r in bronze]).rows
    marts = build_marts({"fire": silver}, [AOI])
    serving = serve_wildfire_daily(marts["kpi_wildfire_aoi_daily"])
    if defect == "mapping":
        silver[0]["brightness"] = None
    if defect == "ledger":
        marts["fire_aoi_attribution"] = []
    if defect == "gold":
        marts["kpi_wildfire_aoi_daily"][0]["detections"] += 1
    if defect == "serving":
        serving[0]["detections"] += 1
    now = NOW.replace(day=1, month=11) if defect == "stale" else NOW
    report = fire_readiness(bronze, silver, marts, [AOI], now, serving)
    assert report["technical_status"] == "blocked"
