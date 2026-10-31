from datetime import date, datetime, timedelta, timezone
import os
import sys
from pathlib import Path
from uuid import uuid4

import pandas as pd
import pytest

from feature_store.database import configure_registry_url, connect, initialize_source_tables
from feature_store.materialize.temporal import add_temporal_features
from feature_store.materialize import gold_sync
from feature_store.quality.climate import (
    climate_distribution_report,
    validate_climate_feature_rows,
)

REPO_PATH = Path(
    os.environ.get(
        "FEAST_REPO_PATH",
        str(Path(__file__).parents[1] / "feature_repo"),
    )
)
if str(REPO_PATH) not in sys.path:
    sys.path.insert(0, str(REPO_PATH))

from entities import ENTITIES, aoi  # noqa: E402
from feature_views import (  # noqa: E402
    FEATURE_SERVICES,
    FEATURE_VIEWS,
    air_quality_aoi_daily,
    climate_indicator_aoi_daily,
    dust_aoi_daily,
    vegetation_health_aoi_daily,
    wildfire_aoi_daily,
)
from feast import FeatureStore  # noqa: E402


def test_climate_views_reuse_aoi_and_are_registered_with_temporal_fields():
    views = {view.name: view for view in FEATURE_VIEWS}
    expected_names = {
        "air_quality_aoi_daily",
        "dust_aoi_daily",
        "climate_indicator_aoi_daily",
        "vegetation_health_aoi_daily",
    }

    assert expected_names.issubset(views)
    for name in expected_names:
        assert views[name].entities == [aoi.name]

    air_fields = {field.name for field in air_quality_aoi_daily.schema}
    dust_fields = {field.name for field in dust_aoi_daily.schema}
    climate_fields = {field.name for field in climate_indicator_aoi_daily.schema}
    vegetation_fields = {field.name for field in vegetation_health_aoi_daily.schema}
    assert {"pm25_mean", "pm10_mean", "no2_column_mean", "aqi_band", "pm25_7d_mean"} <= air_fields
    assert {"aod_mean", "wind_speed_mean", "wind_dir_dominant", "transport_flag"} <= dust_fields
    assert {"lst_anomaly_c", "ndvi_mean", "sst_anomaly_c"} <= climate_fields
    assert {"ndvi_trend_30d", "crop_stress_flag"} <= vegetation_fields
    assert any(
        service.name == "climate_dust_training_service"
        for service in FEATURE_SERVICES
    )


def test_temporal_features_use_calendar_windows_and_report_observation_gaps():
    rows = add_temporal_features(
        [
            {"aoi_key": "AOI-1", "date_key": "2026-01-10", "pm25_mean": 20.0},
            {"aoi_key": "AOI-1", "date_key": date(2026, 1, 1), "pm25_mean": 10.0},
            {"aoi_key": "AOI-1", "date_key": "2026-01-03", "pm25_mean": 16.0},
        ],
        rolling_windows={"pm25_mean": (7, 30)},
    )

    assert rows[-1]["date_key"] == "2026-01-10"
    assert rows[-1]["pm25_7d_mean"] == 20.0
    assert rows[-1]["pm25_30d_mean"] == pytest.approx(46 / 3)
    assert rows[-1]["pm25_change_per_day"] == pytest.approx(4 / 7)
    assert rows[-1]["days_since_previous_observation"] == 7


def test_temporal_features_reject_duplicate_aoi_date_grain():
    with pytest.raises(ValueError, match="Duplicate climate serving row"):
        add_temporal_features(
            [
                {"aoi_key": "AOI-1", "date_key": "2026-01-01", "aod_mean": 0.2},
                {"aoi_key": "AOI-1", "date_key": "20260101", "aod_mean": 0.3},
            ],
            rolling_windows={"aod_mean": (7,)},
        )


def test_climate_quality_checks_nulls_ranges_and_serving_enums():
    rows = [
        {
            "aoi_key": "AOI-1",
            "event_timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "pm25_mean": 15.0,
            "pm10_mean": 30.0,
            "aqi_band": "Good",
        },
        {
            "aoi_key": "AOI-2",
            "event_timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "pm25_mean": 15.0,
            "pm10_mean": 30.0,
            "aqi_band": "not-a-serving-band",
        },
        {
            "aoi_key": "AOI-3",
            "event_timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "pm25_mean": 2500.0,
            "pm10_mean": 30.0,
            "aqi_band": "Good",
        },
    ]

    errors = validate_climate_feature_rows("air_quality_aoi_daily", rows)
    assert any("aqi_band" in error for error in errors)
    assert any("pm25_mean" in error for error in errors)


def test_climate_distribution_report_checks_psi_and_skew():
    report = climate_distribution_report(
        {"pm25_mean": [1.0, 2.0, 3.0, 4.0]},
        {"pm25_mean": [10.0, 10.0, 10.0, 20.0]},
    )

    assert report["pm25_mean"]["psi_status"] == "warn"
    assert report["pm25_mean"]["skew_status"] == "warn"


def test_climate_sync_preserves_serving_lineage_and_event_time(monkeypatch, tmp_path):
    class _Cursor:
        def __init__(self):
            self.statement = ""
            self.rows = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def executemany(self, statement, rows):
            self.statement = statement
            self.rows = rows

    class _Connection:
        def __init__(self):
            self.recorded_cursor = _Cursor()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def cursor(self):
            return self.recorded_cursor

    connection = _Connection()
    monkeypatch.setattr(gold_sync, "connect", lambda: connection)
    event_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    database_path = tmp_path / "serving.duckdb"
    database_path.touch()
    result = gold_sync._sync_climate_product(
        "serving_air_quality_daily",
        gold_sync._CLIMATE_PRODUCTS["serving_air_quality_daily"],
        [
            {
                "aoi_key": "AOI-1",
                "date_key": event_time.date(),
                "pm25_mean": 10.0,
                "pm10_mean": 20.0,
                "aqi_band": "Good",
            }
        ],
        database_path,
    )

    assert result.status == "blocked"
    assert result.rows_written == 1
    assert "source_air_quality_daily" in connection.recorded_cursor.statement
    assert connection.recorded_cursor.rows[0][1] == event_time
    assert connection.recorded_cursor.rows[0][2] == event_time
    assert connection.recorded_cursor.rows[0][4] == 10.0
    assert connection.recorded_cursor.rows[0][4 + 8] is None
    assert connection.recorded_cursor.rows[0][-4] is not None
    assert "serving_air_quality_daily" in connection.recorded_cursor.rows[0][-1]


def test_climate_sync_reads_only_serving_product_tables(monkeypatch, tmp_path):
    import duckdb

    database_path = tmp_path / "test_serving.duckdb"
    with duckdb.connect(str(database_path)) as database:
        database.execute("CREATE SCHEMA serving")
        database.execute(
            """
            CREATE TABLE serving.serving_air_quality_daily (
                aoi_key VARCHAR,
                date_key DATE,
                pm25_mean DOUBLE,
                pm10_mean DOUBLE,
                aqi_band VARCHAR
            )
            """
        )
        database.execute(
            """
            INSERT INTO serving.serving_air_quality_daily
            VALUES ('AOI-1', DATE '2026-01-01', 10.0, 20.0, 'Good')
            """
        )

    class _Cursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def executemany(self, statement, rows):
            self.rows = rows

    class _Connection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def cursor(self):
            return _Cursor()

    monkeypatch.setattr(gold_sync, "_serving_db_path", lambda: database_path)
    monkeypatch.setattr(gold_sync, "connect", _Connection)
    results = gold_sync.sync_climate_serving_products()

    assert [result.source for result in results] == [
        "serving_air_quality_daily",
        "serving_dust_event_daily",
        "serving_climate_indicator_daily",
        "serving_vegetation_health_daily",
    ]
    assert results[0].rows_written == 1
    assert results[0].status == "blocked"
    assert all(result.status == "no_data" for result in results[1:])


def test_climate_and_eo_features_support_point_in_time_and_online_retrieval():
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

    marker = f"TEST-AOI-{uuid4().hex[:12]}"
    first = datetime(2026, 6, 1, tzinfo=timezone.utc)
    second = datetime(2026, 6, 2, tzinfo=timezone.utc)
    source_reference = "feature_store/tests/test_climate_features.py"
    created = first + timedelta(hours=1)
    feature_rows = [
        (marker, first, 12.0, 0.3),
        (marker, second, 24.0, 0.8),
    ]
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO feast.source_air_quality_daily (
                    aoi_key, event_timestamp, created_timestamp, feature_date,
                    pm25_mean, pm10_mean, o3_mean, station_count, aqi_band,
                    data_nature, readiness_status, source_reference
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (aoi_key, event_timestamp) DO UPDATE SET
                    created_timestamp = EXCLUDED.created_timestamp,
                    feature_date = EXCLUDED.feature_date,
                    pm25_mean = EXCLUDED.pm25_mean,
                    pm10_mean = EXCLUDED.pm10_mean,
                    o3_mean = EXCLUDED.o3_mean,
                    station_count = EXCLUDED.station_count,
                    aqi_band = EXCLUDED.aqi_band,
                    data_nature = EXCLUDED.data_nature,
                    readiness_status = EXCLUDED.readiness_status,
                    source_reference = EXCLUDED.source_reference
                """,
                [
                    (
                        marker,
                        timestamp,
                        timestamp + timedelta(hours=1),
                        timestamp.date().isoformat(),
                        pm25,
                        pm25 * 2,
                        pm25 / 2,
                        3,
                        "Good",
                        "synthetic_test",
                        "blocked",
                        source_reference,
                    )
                    for marker, timestamp, pm25, _ in feature_rows
                ],
            )
            cursor.executemany(
                """
                INSERT INTO feast.source_dust_daily (
                    aoi_key, event_timestamp, created_timestamp, feature_date,
                    aod_mean, valid_fraction, wind_speed_mean,
                    wind_direction_dominant, wind_dir_dominant,
                    data_nature, readiness_status, source_reference
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (aoi_key, event_timestamp) DO UPDATE SET
                    created_timestamp = EXCLUDED.created_timestamp,
                    feature_date = EXCLUDED.feature_date,
                    aod_mean = EXCLUDED.aod_mean,
                    valid_fraction = EXCLUDED.valid_fraction,
                    wind_speed_mean = EXCLUDED.wind_speed_mean,
                    wind_dir_dominant = EXCLUDED.wind_dir_dominant,
                    data_nature = EXCLUDED.data_nature,
                    readiness_status = EXCLUDED.readiness_status,
                    source_reference = EXCLUDED.source_reference
                """,
                [
                    (
                        marker,
                        timestamp,
                        timestamp + timedelta(hours=1),
                        timestamp.date().isoformat(),
                        aod,
                        0.9,
                        5.0,
                        180.0,
                        180.0,
                        "synthetic_test",
                        "blocked",
                        source_reference,
                    )
                    for marker, timestamp, _, aod in feature_rows
                ],
            )
            cursor.executemany(
                """
                INSERT INTO feast.source_climate_indicator_daily (
                    aoi_key, event_timestamp, created_timestamp, feature_date,
                    lst_c, lst_anomaly_c, sst_c, sst_anomaly_c, ndvi_mean,
                    evi_mean, ndwi_mean, data_nature, readiness_status,
                    source_reference
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        marker,
                        timestamp,
                        timestamp + timedelta(hours=1),
                        timestamp.date().isoformat(),
                        30.0,
                        anomaly,
                        20.0,
                        0.2,
                        ndvi,
                        ndvi / 2,
                        0.1,
                        "synthetic_test",
                        "blocked",
                        source_reference,
                    )
                    for marker, timestamp, anomaly, ndvi in (
                        (marker, first, 1.0, 0.4),
                        (marker, second, 2.0, 0.6),
                    )
                ],
            )
            cursor.executemany(
                """
                INSERT INTO feast.source_vegetation_health_daily (
                    aoi_key, event_timestamp, created_timestamp, feature_date,
                    ndvi_mean, ndvi_max, evi_mean, ndvi_trend_30d,
                    valid_pixel_fraction, ndvi_health_band, crop_stress_flag,
                    data_nature, readiness_status, source_reference
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        marker,
                        timestamp,
                        timestamp + timedelta(hours=1),
                        timestamp.date().isoformat(),
                        ndvi,
                        ndvi + 0.1,
                        ndvi / 2,
                        0.02,
                        0.9,
                        3,
                        False,
                        "synthetic_test",
                        "blocked",
                        source_reference,
                    )
                    for marker, timestamp, ndvi in (
                        (marker, first, 0.4),
                        (marker, second, 0.6),
                    )
                ],
            )
            cursor.execute(
                """
                INSERT INTO feast.source_wildfire_aoi_daily (
                    aoi_key, event_timestamp, created_timestamp, feature_date,
                    detections, mean_frp, max_frp, ems_corroborated, area_km2,
                    data_nature, readiness_status, source_reference
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (aoi_key, event_timestamp) DO UPDATE SET
                    created_timestamp = EXCLUDED.created_timestamp,
                    feature_date = EXCLUDED.feature_date,
                    detections = EXCLUDED.detections,
                    mean_frp = EXCLUDED.mean_frp,
                    max_frp = EXCLUDED.max_frp,
                    data_nature = EXCLUDED.data_nature,
                    readiness_status = EXCLUDED.readiness_status,
                    source_reference = EXCLUDED.source_reference
                """,
                (
                    marker,
                    first,
                    created,
                    first.date().isoformat(),
                    2,
                    6.0,
                    9.0,
                    False,
                    4.0,
                    "synthetic_test",
                    "blocked",
                    source_reference,
                ),
            )

    try:
        store.materialize(
            start_date=first,
            end_date=second + timedelta(days=1),
            feature_views=[
                air_quality_aoi_daily.name,
                dust_aoi_daily.name,
                climate_indicator_aoi_daily.name,
                vegetation_health_aoi_daily.name,
                wildfire_aoi_daily.name,
            ],
        )
        entity_frame = pd.DataFrame(
            [
                {
                    "aoi_key": marker,
                    "event_timestamp": first + timedelta(hours=12),
                    "label": 0,
                },
                {
                    "aoi_key": marker,
                    "event_timestamp": second + timedelta(hours=12),
                    "label": 1,
                },
            ]
        )
        historical = store.get_historical_features(
            entity_df=entity_frame,
            features=[
                "wildfire_aoi_daily:max_frp",
                "air_quality_aoi_daily:pm25_mean",
                "dust_aoi_daily:aod_mean",
                "dust_aoi_daily:wind_speed_mean",
                "climate_indicator_aoi_daily:lst_anomaly_c",
                "vegetation_health_aoi_daily:ndvi_mean",
            ],
        ).to_df()
        assert historical["air_quality_aoi_daily__pm25_mean"].tolist() == [12.0, 24.0]
        assert historical["dust_aoi_daily__aod_mean"].tolist() == [0.3, 0.8]
        assert historical["wildfire_aoi_daily__max_frp"].tolist() == [9.0, 9.0]
        assert historical["dust_aoi_daily__wind_speed_mean"].tolist() == [5.0, 5.0]
        assert historical["climate_indicator_aoi_daily__lst_anomaly_c"].tolist() == [1.0, 2.0]
        assert historical["vegetation_health_aoi_daily__ndvi_mean"].tolist() == [0.4, 0.6]

        online = store.get_online_features(
            features=[
                "air_quality_aoi_daily:pm25_mean",
                "dust_aoi_daily:aod_mean",
                "climate_indicator_aoi_daily:lst_anomaly_c",
                "vegetation_health_aoi_daily:ndvi_mean",
            ],
            entity_rows=[{"aoi_key": marker}],
        ).to_dict()
        assert online["air_quality_aoi_daily__pm25_mean"] == pytest.approx([24.0])
        assert online["dust_aoi_daily__aod_mean"] == pytest.approx([0.8])
        assert online["climate_indicator_aoi_daily__lst_anomaly_c"] == pytest.approx([2.0])
        assert online["vegetation_health_aoi_daily__ndvi_mean"] == pytest.approx([0.6])
    finally:
        with connect() as connection:
            for table in (
                "source_air_quality_daily",
                "source_dust_daily",
                "source_climate_indicator_daily",
                "source_vegetation_health_daily",
                "source_wildfire_aoi_daily",
            ):
                connection.execute(
                    f"DELETE FROM feast.{table} WHERE aoi_key = %s AND source_reference = %s",
                    (marker, source_reference),
                )
            for view_name in (
                "air_quality_aoi_daily",
                "dust_aoi_daily",
                "climate_indicator_aoi_daily",
                "vegetation_health_aoi_daily",
                "wildfire_aoi_daily",
            ):
                table_name = f"feast.space_mission_features_{view_name}"
                exists = connection.execute(
                    "SELECT to_regclass(%s)",
                    (table_name,),
                ).fetchone()[0]
                if exists:
                    connection.execute(
                        f"""
                        DELETE FROM {table_name}
                        WHERE POSITION(convert_to(%s, 'UTF8') IN entity_key) > 0
                        """,
                        (marker,),
                    )
