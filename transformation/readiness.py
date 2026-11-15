"""Credential-free live inventory and fire-product readiness evidence."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from transformation.batch.bronze_to_silver import clean_fire, silver_fire
from transformation.batch.silver_to_gold import (
    fire_aoi_attribution, gold_earth_observation, gold_wildfire_aoi,
)
from transformation.common.io import unwrap_bronze
from transformation.timeseries.time_series import parse_ts

#: FIRMS event-time freshness objective (hours), approved 2026-11-15: one
#: polar-orbiting VIIRS sensor gives about two passes a day, so 6 h was not
#: attainable. Matches serving ``FIRMS_MAX_OBSERVATION_AGE_HOURS`` and the dbt
#: var ``wildfire_max_observation_age_hours``.
FIRMS_FRESHNESS_OBJECTIVE_HOURS = 24.0

# Explicit product mappings, not claims that a designed catalog entry is live.
CATALOG_PATHS = {
    6: ("ingestion/api/gee_sentinel2.py", ["SENTINELHUB"], ["silver_scene"]),
    8: ("ingestion/api/landsat.py", ["LANDSAT"], ["silver_scene"]),
    9: ("ingestion/api/nasa_firms.py", ["FIRMS"], ["silver_fire"]),
    10: ("ingestion/api/gee_aod.py", ["MODIS_AOD"], ["silver_aerosol"]),
    11: ("ingestion/api/nasa_firms.py", ["FIRMS"], ["silver_fire"]),
    12: ("ingestion/file/file_loader.py", ["EMS"], ["silver_ems_aoi"]),
    13: ("ingestion/api/gee_sentinel2.py", ["SENTINELHUB_STATS"], ["silver_index"]),
    14: ("ingestion/api/noaa_swpc.py", ["SWPC"], ["silver_space_weather"]),
    20: ("ingestion/api/celestrak.py", ["CELESTRAK"], []),
    35: ("ingestion/api/nasa_power.py", ["POWER"], ["silver_wind"]),
    40: ("ingestion/api/openaq.py", ["OPENAQ"], ["silver_air_quality"]),
    44: ("ingestion/simulation/telemetry_generator.py", ["satellite_telemetry"],
         ["silver_telemetry"]),
}
GOLD_PATHS = {
    "silver_fire": ["fire_aoi_attribution", "kpi_wildfire_aoi_daily", "kpi_eo_daily"],
    "silver_scene": ["fact_scene_catalog"],
    "silver_index": ["kpi_flood_aoi_daily", "fact_vegetation_health_daily",
                     "fact_climate_indicator_daily"],
    "silver_air_quality": ["fact_air_quality_daily"],
    "silver_aerosol": ["fact_dust_event_daily"],
    "silver_wind": ["fact_dust_event_daily"],
    "silver_space_weather": ["fact_weather_impact"],
    "silver_telemetry": ["fact_sat_health"],
}


def catalog_entries(markdown: str) -> list[dict[str, Any]]:
    entries = [
        {"catalog_id": int(number), "name": name.strip()}
        for number, name in re.findall(r"^\|\s*(\d+)\s*\|\s*([^|]+)\|", markdown, re.M)
    ]
    ids = [entry["catalog_id"] for entry in entries]
    if sorted(ids) != list(range(1, 46)):
        raise ValueError("Source catalog must contain exactly the unique entries 1-45")
    return entries


@dataclass
class DatasetProfile:
    path: str
    row_count: int = 0
    event_min: datetime | None = None
    event_max: datetime | None = None
    last_ingest: datetime | None = None
    invalid_event_times: int = 0
    missing_event_times: int = 0
    dates: set[str] = field(default_factory=set)
    schemas: set[str] = field(default_factory=set)

    def add(self, row: dict[str, Any]) -> None:
        self.row_count += 1
        payload = row.get("payload", row)
        fields = sorted(payload) if isinstance(payload, dict) else ["<non-object>"]
        self.schemas.add(hashlib.sha256(json.dumps(fields).encode()).hexdigest()[:16])
        event = next((row.get(key) for key in
                      ("_event_ts", "event_ts", "timestamp", "date_key", "window_start")
                      if row.get(key) not in (None, "")), None)
        ts = parse_ts(event)
        if ts is None:
            self.missing_event_times += int(event in (None, ""))
            self.invalid_event_times += int(event not in (None, ""))
        else:
            self.event_min = min(self.event_min, ts) if self.event_min else ts
            self.event_max = max(self.event_max, ts) if self.event_max else ts
            self.dates.add(ts.date().isoformat())
        ingest = parse_ts(row.get("_ingest_ts"))
        if ingest:
            self.last_ingest = max(self.last_ingest, ingest) if self.last_ingest else ingest

    def report(self, now: datetime) -> dict[str, Any]:
        return {
            "path": self.path, "row_count": self.row_count,
            "event_time_min": self.event_min.isoformat() if self.event_min else None,
            "event_time_max": self.event_max.isoformat() if self.event_max else None,
            "distinct_dates": len(self.dates),
            "freshness_hours": round((now - self.event_max).total_seconds() / 3600, 3)
            if self.event_max else None,
            "last_successful_landing": self.last_ingest.isoformat() if self.last_ingest else None,
            "missing_event_times": self.missing_event_times,
            "invalid_event_times": self.invalid_event_times,
            "observed_field_schema_versions": sorted(self.schemas),
            "schema_version_kind": "sha256-field-names-v1; not a declared schema contract",
        }


def source_inventory(entries: list[dict[str, Any]], profiles: dict[str, DatasetProfile],
                     implemented_files: set[str], now: datetime) -> list[dict[str, Any]]:
    out = []
    for entry in entries:
        code, bronze, silver = CATALOG_PATHS.get(entry["catalog_id"], (None, [], []))
        implemented = code in implemented_files if code else False
        paths = [f"s3://bronze/{p}" for p in bronze] + [f"s3://silver/{p}" for p in silver]
        paths += [f"s3://gold/{p}" for entity in silver for p in GOLD_PATHS.get(entity, [])]
        observed = [profiles[path] for path in paths if path in profiles]
        landings = [p.last_ingest for p in observed if p.last_ingest is not None]
        latest = max(landings) if landings else None
        recent = latest is not None and now - timedelta(hours=24) <= latest <= now
        out.append({
            **entry, "owner": "data-eng", "implementation_path": code,
            "expected_paths": paths, "observed_paths": [p.path for p in observed],
            "designed": True, "implemented": implemented,
            "populated": any(p.row_count for p in observed),
            "refreshable": True if recent and implemented else None,
            "source_access_status": "recent_landing_evidence" if recent else
            "not_implemented" if not implemented else "unknown",
            "last_successful_landing": latest.isoformat() if latest else None,
            "analysis_ready": False,
            "limitations": "No active upstream probe or domain certification. Shared paths "
            "are not additive; catalog MODIS mapping covers AOD only, not all imagery.",
        })
    return out


def fire_readiness(bronze: list[dict[str, Any]], silver: list[dict[str, Any]],
                   gold: dict[str, list[dict[str, Any]]], aois: list[dict[str, Any]],
                   now: datetime, serving: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    raw = [unwrap_bronze(r) if "payload" in r else r for r in bronze]
    expected = silver_fire(raw)
    by_key = {r["fire_key"]: r for r in expected.rows}
    candidates = {}
    for record in raw:
        cleaned = clean_fire(record).record
        if cleaned is not None:
            candidates[(cleaned["fire_key"], cleaned.get("_ingest_id"),
                        cleaned.get("_batch_id"))] = cleaned
    fields = ("brightness", "brightness_source_field", "brightness_status", "brightness_unit",
              "bright_ti5", "bright_t31", "frp", "confidence", "_ingest_id", "_batch_id",
              "_source", "_ingest_ts")
    mapping_errors = 0
    for row in silver:
        origin = candidates.get((row.get("fire_key"), row.get("_ingest_id"),
                                 row.get("_batch_id")))
        if origin is None or any(row.get(f) != origin.get(f) for f in fields):
            mapping_errors += 1
    expected_attribution = fire_aoi_attribution(silver, aois)
    actual_attribution = gold.get("fire_aoi_attribution", [])
    expected_wildfire = gold_wildfire_aoi(silver, aois)
    actual_wildfire = gold.get("kpi_wildfire_aoi_daily", [])

    def canonical(rows: list[dict[str, Any]]) -> list[str]:
        return sorted(json.dumps(r, sort_keys=True, default=str) for r in rows)

    statuses = Counter(r["match_status"] for r in expected_attribution)
    assignments = sum(r["match_count"] for r in expected_attribution)
    profile = DatasetProfile("s3://silver/silver_fire")
    for row in silver:
        profile.add(row)
    freshness = profile.report(now)["freshness_hours"]
    serving_fields = ("aoi_key", "date_key", "detections", "mean_frp", "max_frp")
    serving_matches = serving is not None and canonical([
        {k: r.get(k) for k in serving_fields} for r in serving
    ]) == canonical([{k: r.get(k) for k in serving_fields} for r in actual_wildfire])
    gates = {
        "required_source_populated": bool(bronze and silver),
        "bronze_to_silver_keys": len(silver) == len(by_key)
        and {r.get("fire_key") for r in silver} == set(by_key),
        "measurement_and_lineage_mapping": mapping_errors == 0,
        "silver_keys_unique": len({r.get("fire_key") for r in silver}) == len(silver),
        "persisted_attribution_matches": canonical(actual_attribution) == canonical(expected_attribution),
        "every_detection_accounted": sum(statuses.values()) == len(silver)
        and not statuses["invalid_date"],
        "gold_aoi_reconciliation": canonical(actual_wildfire) == canonical(expected_wildfire),
        "gold_grid_reconciliation": canonical(gold.get("kpi_eo_daily", []))
        == canonical(gold_earth_observation(silver)),
        "serving_reconciliation": serving_matches,
        "freshness_within_objective": freshness is not None
        and 0 <= freshness <= FIRMS_FRESHNESS_OBJECTIVE_HOURS,
    }
    completeness = {
        field: {"missing_count": sum(r.get(field) is None for r in silver),
                "null_fraction": sum(r.get(field) is None for r in silver) / len(silver)
                if silver else None}
        for field in ("brightness", "frp", "confidence", "_ingest_id", "_batch_id")
    }
    return {
        "product": "serving_wildfire_daily",
        "business_question": "How many detected thermal anomalies intersect each configured AOI per UTC day?",
        "grain": "AOI / UTC date; overlapping AOIs may count a detection more than once",
        "data_nature": "real/open FIRMS observations; derived aggregates; curated reference AOIs",
        "lineage": ["s3://bronze/FIRMS", "s3://silver/silver_fire",
                    "s3://gold/fire_aoi_attribution", "s3://gold/kpi_wildfire_aoi_daily",
                    "serving/dbt/serving.duckdb:serving_wildfire_daily"],
        "time_coverage": profile.report(now),
        "counts": {"bronze_rows": len(bronze), "quarantined": len(expected.quarantine),
                   "duplicates_removed": len(bronze) - len(expected.quarantine) - len(expected.rows),
                   "silver_detections": len(silver), "matched": statuses["matched"],
                   "unmatched": statuses["unmatched"], "invalid_date": statuses["invalid_date"],
                   "overlapping_detections": sum(r["match_count"] > 1 for r in expected_attribution),
                   "aoi_assignments": assignments,
                   "gold_detections": sum(r["detections"] for r in actual_wildfire),
                   "serving_rows": len(serving) if serving is not None else None},
        "coverage_by_aoi": dict(Counter(k for r in expected_attribution for k in r["aoi_keys"])),
        "key_field_completeness": completeness,
        "brightness_status_counts": dict(Counter(r.get("brightness_status") for r in silver)),
        "mapping_error_count": mapping_errors,
        "representative_query": {
            "purpose": "Review the largest AOI/day detection counts; not a hazard confirmation.",
            "sql": "SET schema = 'serving'; "
                   "SELECT aoi_key, date_key, detections, mean_frp, max_frp "
                   "FROM serving_wildfire_daily ORDER BY detections DESC, aoi_key, date_key LIMIT 5",
            "results": [
                {key: row.get(key) for key in serving_fields}
                for row in sorted(serving or [], key=lambda r: (
                    -r["detections"], r["aoi_key"], r["date_key"]
                ))[:5]
            ],
            "domain_review_status": "pending",
        },
        "technical_gates": gates,
        "technical_status": "pass" if all(gates.values()) else "blocked",
        "quality_status": "blocked",
        "analysis_ready": False,
        "limitations": [
            "Domain owner has not approved grain, completeness bounds, or an acceptance scenario.",
            "AOI seed is curated rectangular reference data, not independently verified EMS activation evidence.",
            "Unmatched detections remain in the attribution ledger; no AOI is invented to improve match rate.",
            "Matching uses WGS84 lon/lat, outer edges included, hole interiors/edges excluded; "
            "no reprojection, antimeridian polygons, temporal activation matching, or burned-area inference.",
            "Brightness is VIIRS I4 or MODIS channel-21/22 temperature (K), not interchangeable radiance; "
            "FRP (MW) and confidence remain independent. Confidence categories use the existing numeric mapping.",
            "A successful snapshot is a bounded observation window, not a transactional whole-lake snapshot.",
        ],
    }
