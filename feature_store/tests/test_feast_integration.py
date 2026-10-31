from datetime import datetime, timedelta, timezone
import os
import sys
from pathlib import Path
from uuid import uuid4

import pandas as pd
import pytest

from feature_store.database import configure_registry_url, connect, initialize_source_tables

REPO_PATH = Path(
    os.environ.get(
        "FEAST_REPO_PATH",
        str(Path(__file__).parents[1] / "feature_repo"),
    )
)
if str(REPO_PATH) not in sys.path:
    sys.path.insert(0, str(REPO_PATH))

from entities import ENTITIES  # noqa: E402
from feature_views import FEATURE_SERVICES, FEATURE_VIEWS, satellite_health_daily  # noqa: E402
from feast import FeatureStore  # noqa: E402


def test_postgres_offline_point_in_time_and_online_materialization():
    required_settings = (
        "POSTGRES_HOST",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    )
    if not all(os.environ.get(setting) for setting in required_settings):
        pytest.skip("Configured PostgreSQL is required for Feast integration tests.")

    configure_registry_url()
    initialize_source_tables()
    store = FeatureStore(repo_path=str(REPO_PATH))
    store.apply([*ENTITIES, *FEATURE_VIEWS, *FEATURE_SERVICES])

    key = f"TEST-SAT-{uuid4().hex[:12]}"
    first = datetime(2026, 6, 1, tzinfo=timezone.utc)
    second = datetime(2026, 6, 2, tzinfo=timezone.utc)
    rows = [
        (
            key,
            first,
            first + timedelta(hours=1),
            "2026-06-01",
            20,
            2,
            0.1,
            0.9,
            0.2,
            "synthetic_test",
            "demo_only",
            "feature_store/tests/test_feast_integration.py",
        ),
        (
            key,
            second,
            second + timedelta(hours=1),
            "2026-06-02",
            20,
            6,
            0.3,
            0.7,
            0.8,
            "synthetic_test",
            "demo_only",
            "feature_store/tests/test_feast_integration.py",
        ),
    ]
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
            INSERT INTO feast.source_satellite_health (
                sat_key, event_timestamp, created_timestamp, feature_date, samples,
                anomaly_samples, anomaly_density, health_score,
                battery_voltage_drift, data_nature, readiness_status, source_reference
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                rows,
            )

    try:
        store.materialize(
            start_date=first,
            end_date=second + timedelta(days=1),
            feature_views=[satellite_health_daily.name],
        )
        entity_frame = pd.DataFrame(
            [
                {
                    "sat_key": key,
                    "event_timestamp": first + timedelta(hours=12),
                    "label": 0,
                },
                {
                    "sat_key": key,
                    "event_timestamp": second + timedelta(hours=12),
                    "label": 1,
                },
            ]
        )
        historical = store.get_historical_features(
            entity_df=entity_frame,
            features=["satellite_health_daily:health_score"],
        ).to_df()
        health_column = next(
            column for column in historical.columns if column.endswith("health_score")
        )
        assert historical[health_column].tolist() == [0.9, 0.7]

        online = store.get_online_features(
            features=["satellite_health_daily:health_score"],
            entity_rows=[{"sat_key": key}],
        ).to_dict()
        health_key = next(
            name for name in online if name.endswith("health_score")
        )
        assert online[health_key] == pytest.approx([0.7], abs=1e-6)
    finally:
        with connect() as connection:
            connection.execute(
                """
                DELETE FROM feast.source_satellite_health
                WHERE sat_key = %s AND source_reference = %s
                """,
                (key, "feature_store/tests/test_feast_integration.py"),
            )
            connection.execute(
                """
                DELETE FROM feast.space_mission_features_satellite_health_daily
                WHERE POSITION(convert_to('TEST-SAT-', 'UTF8') IN entity_key) > 0
                """
            )
