"""One-command, infra-free demo of the transformation pipeline.

Exercises the full Medallion flow **in-memory** (no Spark, Kafka, or MinIO):

    synthetic Bronze -> Silver (clean/dedup) -> Gold (aggregates) -> Features

Reuses the Phase 8 ingestion generators so the demo data matches real record
shapes, then runs every pure-Python transform and writes inspectable output to
``transformation/output/``.

Run:
    python -m transformation.scripts.run_local_demo --records 60
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from transformation.batch.bronze_to_silver import (
    silver_orbit,
    silver_space_weather,
    silver_telemetry,
)
from transformation.batch.silver_to_gold import (
    gold_satellite_health,
    gold_space_weather_impact,
)
from transformation.cleaning.validation_framework import (
    expect_not_null,
    expect_unique,
    run_checkpoint,
)
from transformation.common.io import write_json, write_ndjson
from transformation.common.lineage import LineageRecord, new_run_id
from transformation.common.logging_setup import get_logger
from transformation.config.settings import settings
from transformation.features.feature_engineering import (
    orbit_features,
    satellite_health_features,
    space_weather_features,
)

log = get_logger("demo")
OUTPUT_DIR = settings.local_output


def _generate_bronze(records: int):
    """Produce Bronze-shaped records using the ingestion generators if available,
    else a small built-in fallback so the demo never hard-fails offline."""
    try:
        from ingestion.common.envelope import build_envelope, new_batch_id
        from ingestion.common.io import unwrap_bronze  # type: ignore
    except Exception:  # noqa: BLE001
        build_envelope = None  # type: ignore

    from datetime import datetime, timedelta, timezone

    from transformation.common.io import unwrap_bronze as _unwrap

    try:
        from ingestion.simulation.orbit_simulator import OrbitSimulator
        from ingestion.simulation.space_weather_generator import SpaceWeatherGenerator
        from ingestion.simulation.telemetry_generator import TelemetryGenerator
        start = datetime(2026, 6, 1, tzinfo=timezone.utc)
        tel = list(TelemetryGenerator(seed=42, failure_rate=0.08,
                                      start_time=start).stream(max_records=records))
        orb = list(OrbitSimulator(interval_s=30).stream(max_records=max(6, records // 4)))
        wea = list(SpaceWeatherGenerator().stream(max_records=max(5, records // 6)))
    except Exception:  # noqa: BLE001 - minimal offline fallback
        base = datetime(2026, 6, 1, tzinfo=timezone.utc)
        tel = [{
            "timestamp": (base + timedelta(seconds=i)).isoformat(),
            "satellite_id": f"SAT-00{i % 3 + 1}",
            "sensor_type": "bus_payload",
            "payload": {"battery_voltage": {"value": 28 + (i % 5) * 0.1, "unit": "V",
                                            "status": "ANOMALY" if i % 11 == 0 else "NOMINAL"}},
            "metadata": {"health": "ANOMALY" if i % 11 == 0 else "NOMINAL",
                         "label_anomaly": i % 11 == 0},
        } for i in range(records)]
        orb = [{
            "timestamp": (base + timedelta(seconds=i * 30)).isoformat(),
            "satellite_id": "SAT-001", "latitude": (i % 90), "longitude": (i % 180),
            "altitude_km": 420 + (i % 5),
        } for i in range(max(6, records // 4))]
        wea = [{
            "timestamp": (base + timedelta(minutes=i)).isoformat(), "event_type": "space_weather",
            "kp_index": (i % 9), "flare_class": "M3" if i % 4 == 0 else "B2",
            "geomagnetic_storm": (i % 9) >= 5, "severity": "G1+" if (i % 9) >= 5 else "quiet",
            "source": "synthetic",
        } for i in range(max(5, records // 6))]

    # Wrap in Bronze envelope + unwrap (mirrors the real ingest->transform handoff).
    def wrap(rows, source):
        if build_envelope is None:
            return [_unwrap({"payload": r, "_source": source}) for r in rows]
        batch = new_batch_id(source)
        return [_unwrap(build_envelope(source=source, payload=r, batch_id=batch,
                                       event_ts=r.get("timestamp")).to_dict()) for r in rows]

    return wrap(tel, "TELEMETRY"), wrap(orb, "ORBIT"), wrap(wea, "SPACE_WEATHER")


def run(records: int = 60) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    run_id = new_run_id("demo")
    tel_b, orb_b, wea_b = _generate_bronze(records)

    # Bronze -> Silver
    s_tel = silver_telemetry(tel_b)
    s_orb = silver_orbit(orb_b)
    s_wea = silver_space_weather(wea_b)

    # Quality checkpoint on Silver telemetry (Task 12).
    checkpoint = run_checkpoint(
        s_tel.rows,
        [expect_not_null("event_ts"), expect_not_null("satellite_id"),
         expect_unique(["satellite_id", "event_ts"])],
        name="silver_telemetry",
    )

    # Silver -> Gold
    g_health = gold_satellite_health(s_tel.rows)
    g_weather = gold_space_weather_impact(s_wea.rows, s_tel.rows)

    # Features
    f_health = satellite_health_features(s_tel.rows)
    f_orbit = orbit_features(s_orb.rows)
    f_weather = space_weather_features(s_wea.rows)

    # Persist outputs.
    write_ndjson(OUTPUT_DIR / "silver_telemetry.jsonl", s_tel.rows)
    write_ndjson(OUTPUT_DIR / "silver_orbit.jsonl", s_orb.rows)
    write_ndjson(OUTPUT_DIR / "silver_space_weather.jsonl", s_wea.rows)
    write_ndjson(OUTPUT_DIR / "quarantine.jsonl",
                 s_tel.quarantine + s_orb.quarantine + s_wea.quarantine)
    write_json(OUTPUT_DIR / "gold_satellite_health.json", g_health)
    write_json(OUTPUT_DIR / "gold_space_weather_impact.json", g_weather)
    write_ndjson(OUTPUT_DIR / "features_sat_health.jsonl", f_health)
    write_ndjson(OUTPUT_DIR / "features_orbit.jsonl", f_orbit)
    write_ndjson(OUTPUT_DIR / "features_space_weather.jsonl", f_weather)

    lineage = LineageRecord(
        run_id=run_id, job="demo", layer_from="bronze", layer_to="gold",
        inputs=["telemetry", "orbit", "space_weather"],
        outputs=["silver_*", "gold_satellite_health", "gold_space_weather_impact", "features_*"],
        rows_in=s_tel.rows_in + s_orb.rows_in + s_wea.rows_in,
        rows_out=len(s_tel.rows) + len(s_orb.rows) + len(s_wea.rows),
        rows_rejected=len(s_tel.quarantine) + len(s_orb.quarantine) + len(s_wea.quarantine),
    ).complete()
    write_json(OUTPUT_DIR / "lineage.json", lineage.to_dict())

    summary = {
        "run_id": run_id,
        "silver": {"telemetry": len(s_tel.rows), "orbit": len(s_orb.rows),
                   "space_weather": len(s_wea.rows)},
        "quarantined": lineage.rows_rejected,
        "gold": {"satellite_health_rows": len(g_health),
                 "space_weather_impact_rows": len(g_weather)},
        "features": {"sat_health": len(f_health), "orbit": len(f_orbit),
                     "space_weather": len(f_weather)},
        "checkpoint_passed": checkpoint.passed,
        "checkpoint_failures": checkpoint.failures,
        "output_dir": str(OUTPUT_DIR),
    }
    log.info("transformation demo complete: %s", summary)
    print(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Infra-free transformation demo")
    parser.add_argument("--records", type=int, default=60)
    args = parser.parse_args()
    run(args.records)


if __name__ == "__main__":
    main()
