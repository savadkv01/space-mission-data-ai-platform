"""One-command, infra-free demo of the ingestion pipeline.

Exercises the full logical flow **in-memory** (no Kafka, no MinIO) so the layer
can be validated on any laptop:

    synthetic telemetry -> Bronze envelope -> validation -> cleaned / quarantine

Also demonstrates the orbit and space-weather generators. Writes sample Bronze
output to ``ingestion/output/`` for inspection.

Run:
    python -m ingestion.scripts.run_local_demo --records 30
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ingestion.common.envelope import build_envelope, new_batch_id
from ingestion.common.logging_setup import get_logger
from ingestion.quality.validators import DuplicateTracker, validate_record
from ingestion.simulation.orbit_simulator import OrbitSimulator
from ingestion.simulation.space_weather_generator import SpaceWeatherGenerator
from ingestion.simulation.telemetry_generator import TelemetryGenerator

log = get_logger("demo")
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"


def run(records: int = 30) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    batch_id = new_batch_id("demo")
    dedup = DuplicateTracker()

    telemetry = TelemetryGenerator(seed=42, failure_rate=0.05)
    cleaned, quarantined, bronze_lines = [], [], []

    for record in telemetry.stream(max_records=records):
        env = build_envelope(source="TELEMETRY", payload=record, batch_id=batch_id,
                             event_ts=record["timestamp"])
        bronze_lines.append(env.to_json())
        outcome = validate_record(record, schema="satellite_telemetry",
                                  checksum=env._checksum, dedup=dedup)
        (cleaned if outcome.valid else quarantined).append((record, outcome))

    # Persist a Bronze NDJSON sample (what the raw consumer would land in MinIO).
    (OUTPUT_DIR / "bronze_telemetry_sample.jsonl").write_text("\n".join(bronze_lines), encoding="utf-8")

    orbit = [o for o in OrbitSimulator(interval_s=30).stream(max_records=6)]
    weather = [w for w in SpaceWeatherGenerator().stream(max_records=5)]
    (OUTPUT_DIR / "orbit_sample.json").write_text(json.dumps(orbit, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "space_weather_sample.json").write_text(json.dumps(weather, indent=2), encoding="utf-8")

    summary = {
        "telemetry_records": records,
        "cleaned": len(cleaned),
        "quarantined": len(quarantined),
        "orbit_points": len(orbit),
        "weather_events": len(weather),
        "output_dir": str(OUTPUT_DIR),
    }
    log.info("demo complete: %s", summary)
    print(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Infra-free ingestion demo")
    parser.add_argument("--records", type=int, default=30)
    args = parser.parse_args()
    run(args.records)


if __name__ == "__main__":
    main()
