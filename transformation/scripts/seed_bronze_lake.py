"""Seed enveloped Bronze NDJSON for the full-infra run.

Generates Bronze-envelope records (the exact shape ``run_spark`` reads via
``spark.read.json`` then ``unwrap_bronze``) for telemetry, orbit, and space
weather using the Phase 8 ingestion generators, and writes one NDJSON file per
dataset to a local output directory. A separate step uploads these to MinIO
(``s3://bronze/<dataset>/``) with the MinIO client.

Run from the repo root:
    python -m transformation.scripts.seed_bronze_lake --records 120 --out .bronze_seed
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ingestion.common.envelope import build_envelope, new_batch_id

DATASETS = {
    "TELEMETRY": "satellite_telemetry",
    "ORBIT": "orbit_position",
    "SPACE_WEATHER": "space_weather",
}


def _generate(records: int):
    """Produce raw source records; fall back to a built-in generator offline."""
    start = datetime(2026, 6, 1, tzinfo=timezone.utc)
    try:
        from ingestion.simulation.orbit_simulator import OrbitSimulator
        from ingestion.simulation.space_weather_generator import SpaceWeatherGenerator
        from ingestion.simulation.telemetry_generator import TelemetryGenerator

        tel = list(TelemetryGenerator(seed=42, failure_rate=0.08,
                                      start_time=start).stream(max_records=records))
        orb = list(OrbitSimulator(interval_s=30).stream(max_records=max(6, records // 4)))
        wea = list(SpaceWeatherGenerator().stream(max_records=max(5, records // 6)))
        return tel, orb, wea
    except Exception:  # noqa: BLE001 - minimal offline fallback
        tel = [{
            "timestamp": (start + timedelta(seconds=i)).isoformat(),
            "satellite_id": f"SAT-00{i % 3 + 1}",
            "sensor_type": "bus_payload",
            "payload": {"battery_voltage": {"value": 28 + (i % 5) * 0.1, "unit": "V",
                                            "status": "ANOMALY" if i % 11 == 0 else "NOMINAL"}},
            "metadata": {"health": "ANOMALY" if i % 11 == 0 else "NOMINAL",
                         "label_anomaly": i % 11 == 0},
        } for i in range(records)]
        orb = [{
            "timestamp": (start + timedelta(seconds=i * 30)).isoformat(),
            "satellite_id": "SAT-001", "latitude": (i % 90), "longitude": (i % 180),
            "altitude_km": 420 + (i % 5),
        } for i in range(max(6, records // 4))]
        wea = [{
            "timestamp": (start + timedelta(minutes=i)).isoformat(), "event_type": "space_weather",
            "kp_index": (i % 9), "flare_class": "M3" if i % 4 == 0 else "B2",
            "geomagnetic_storm": (i % 9) >= 5, "severity": "G1+" if (i % 9) >= 5 else "quiet",
            "source": "synthetic",
        } for i in range(max(5, records // 6))]
        return tel, orb, wea


def _envelope_lines(rows, source: str) -> list[str]:
    batch = new_batch_id(source)
    out = []
    for r in rows:
        env = build_envelope(source=source, payload=r, batch_id=batch,
                             event_ts=r.get("timestamp"))
        out.append(json.dumps(env.to_dict(), default=str))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed enveloped Bronze NDJSON")
    parser.add_argument("--records", type=int, default=120)
    parser.add_argument("--out", default=".bronze_seed")
    args = parser.parse_args()

    tel, orb, wea = _generate(args.records)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    sources = {"TELEMETRY": tel, "ORBIT": orb, "SPACE_WEATHER": wea}
    summary = {}
    for source, rows in sources.items():
        dataset = DATASETS[source]
        lines = _envelope_lines(rows, source)
        path = out_dir / f"{dataset}.json"
        path.write_text("\n".join(lines), encoding="utf-8")
        summary[dataset] = len(lines)

    print(json.dumps({"out_dir": str(out_dir.resolve()), "counts": summary}, indent=2))


if __name__ == "__main__":
    main()
