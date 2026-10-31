from __future__ import annotations

from datetime import datetime, timedelta, timezone

from feature_store.database import connect


def seed_satellite_health_demo(now: datetime | None = None) -> int:
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        raise ValueError("Demo seed timestamps must include a timezone.")

    rows = []
    for satellite_number in range(1, 3):
        sat_key = f"SIM-SAT-{satellite_number:03d}"
        for day_offset in range(3, -1, -1):
            event_timestamp = (current_time - timedelta(days=day_offset)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            samples = 24
            anomaly_samples = (satellite_number + day_offset) % 4
            rows.append(
                (
                    sat_key,
                    event_timestamp,
                    current_time,
                    event_timestamp.date().isoformat(),
                    samples,
                    anomaly_samples,
                    anomaly_samples / samples,
                    round(1 - anomaly_samples / (samples * 2), 4),
                    round(0.1 * (satellite_number + day_offset), 4),
                    "synthetic_demo",
                    "demo_only",
                    "feature_store/data/demo_satellite_health",
                )
            )

    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
            """
            INSERT INTO feast.source_satellite_health (
                sat_key, event_timestamp, created_timestamp, feature_date, samples,
                anomaly_samples, anomaly_density, health_score,
                battery_voltage_drift, data_nature, readiness_status, source_reference
            ) VALUES (
                %(sat_key)s, %(event_timestamp)s, %(created_timestamp)s,
                %(feature_date)s, %(samples)s, %(anomaly_samples)s,
                %(anomaly_density)s, %(health_score)s, %(battery_voltage_drift)s,
                %(data_nature)s, %(readiness_status)s, %(source_reference)s
            )
            ON CONFLICT (sat_key, event_timestamp) DO UPDATE SET
                created_timestamp = EXCLUDED.created_timestamp,
                feature_date = EXCLUDED.feature_date,
                samples = EXCLUDED.samples,
                anomaly_samples = EXCLUDED.anomaly_samples,
                anomaly_density = EXCLUDED.anomaly_density,
                health_score = EXCLUDED.health_score,
                battery_voltage_drift = EXCLUDED.battery_voltage_drift,
                data_nature = EXCLUDED.data_nature,
                readiness_status = EXCLUDED.readiness_status,
                source_reference = EXCLUDED.source_reference
                """,
                [
                    {
                        "sat_key": row[0],
                        "event_timestamp": row[1],
                        "created_timestamp": row[2],
                        "feature_date": row[3],
                        "samples": row[4],
                        "anomaly_samples": row[5],
                        "anomaly_density": row[6],
                        "health_score": row[7],
                        "battery_voltage_drift": row[8],
                        "data_nature": row[9],
                        "readiness_status": row[10],
                        "source_reference": row[11],
                    }
                    for row in rows
                ],
            )
    return len(rows)
