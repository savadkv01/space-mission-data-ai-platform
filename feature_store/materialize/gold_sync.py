from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

import pyarrow.dataset as ds
import pyarrow.fs as pafs

from feature_store.database import connect
from feature_store.materialize.temporal import add_temporal_features
from feature_store.quality.climate import validate_climate_feature_rows
from feature_store.readiness import FEATURE_READINESS


@dataclass(frozen=True)
class GoldSyncResult:
    source: str
    status: str
    rows_written: int
    detail: str


def _scene_files(filesystem: pafs.FileSystem) -> list[pafs.FileInfo]:
    try:
        entries = filesystem.get_file_info(
            pafs.FileSelector("gold/fact_scene_catalog", recursive=True)
        )
    except FileNotFoundError:
        return []
    return [
        entry
        for entry in entries
        if entry.type == pafs.FileType.File and entry.path.endswith(".parquet")
    ]


def sync_scene_catalog() -> GoldSyncResult:
    filesystem = pafs.S3FileSystem(
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        endpoint_override=os.environ.get("FEATURE_STORE_S3_ENDPOINT", "minio:9000"),
        scheme=os.environ.get("FEATURE_STORE_S3_SCHEME", "http"),
        region=os.environ.get("AWS_REGION", "us-east-1"),
    )
    files = _scene_files(filesystem)
    if not files:
        return GoldSyncResult(
            source="gold/fact_scene_catalog",
            status="blocked",
            rows_written=0,
            detail="No Gold scene-catalog Parquet files were found; catalog features remain unavailable.",
        )

    table = ds.dataset(
        [entry.path for entry in files],
        filesystem=filesystem,
        format="parquet",
    ).to_table()
    required = {
        "scene_key",
        "date_key",
        "cloud_cover",
        "completeness_score",
        "is_searchable",
    }
    missing = required.difference(table.column_names)
    if missing:
        raise ValueError(f"Gold scene catalog is missing required columns: {sorted(missing)}")

    created_timestamp = datetime.now(timezone.utc)
    rows = []
    for record in table.to_pylist():
        scene_key = record["scene_key"]
        date_key = record["date_key"]
        if scene_key is None or date_key is None:
            continue
        feature_date = date_key.isoformat() if hasattr(date_key, "isoformat") else str(date_key)
        event_timestamp = datetime.fromisoformat(feature_date).replace(tzinfo=timezone.utc)
        rows.append(
            (
                str(scene_key),
                event_timestamp,
                created_timestamp,
                feature_date,
                record["cloud_cover"],
                record["completeness_score"],
                record["is_searchable"],
                "open_source_derived_catalog",
                "restricted",
                f"s3://gold/fact_scene_catalog/{scene_key}",
            )
        )

    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
            INSERT INTO feast.source_scene_catalog (
                scene_key, event_timestamp, created_timestamp, feature_date,
                cloud_cover, completeness_score, is_searchable, data_nature,
                readiness_status, source_reference
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (scene_key, event_timestamp) DO UPDATE SET
                created_timestamp = EXCLUDED.created_timestamp,
                feature_date = EXCLUDED.feature_date,
                cloud_cover = EXCLUDED.cloud_cover,
                completeness_score = EXCLUDED.completeness_score,
                is_searchable = EXCLUDED.is_searchable,
                data_nature = EXCLUDED.data_nature,
                readiness_status = EXCLUDED.readiness_status,
                source_reference = EXCLUDED.source_reference
                """,
                rows,
            )
    return GoldSyncResult(
        source="gold/fact_scene_catalog",
        status="restricted",
        rows_written=len(rows),
        detail="Catalog metadata only; no image-pixel or derived-index claims are enabled.",
    )


_CLIMATE_PRODUCTS = {
    "serving_air_quality_daily": {
        "view": "air_quality_aoi_daily",
        "table": "source_air_quality_daily",
        "rolling": {"pm25_mean": (7, 30), "pm10_mean": (7, 30)},
        "fields": (
            "pm25_mean", "pm25_max", "pm10_mean", "pm10_max",
            "no2_column_mean", "so2_column_mean", "co_column_mean",
            "o3_column_mean", "ch4_column_mean", "station_count",
            "aqi_pm25", "aqi_pm10", "aqi_band", "exceedance_flag",
            "pm25_7d_mean", "pm25_30d_mean", "pm25_change_per_day",
            "pm10_7d_mean", "pm10_30d_mean", "pm10_change_per_day",
        ),
        "mapping": {
            "pm25_mean": "pm25_mean", "pm25_max": "pm25_max",
            "pm10_mean": "pm10_mean", "pm10_max": "pm10_max",
            "no2_column_mean": "no2_column_mean",
            "so2_column_mean": "so2_column_mean",
            "co_column_mean": "co_column_mean",
            "o3_column_mean": "o3_column_mean",
            "ch4_column_mean": "ch4_column_mean",
            "station_count": "station_count", "aqi_pm25": "aqi_pm25",
            "aqi_pm10": "aqi_pm10", "aqi_band": "aqi_band",
            "exceedance_flag": "exceedance_flag",
            "pm25_7d_mean": "pm25_7d_mean",
            "pm25_30d_mean": "pm25_30d_mean",
            "pm25_change_per_day": "pm25_change_per_day",
            "pm10_7d_mean": "pm10_7d_mean",
            "pm10_30d_mean": "pm10_30d_mean",
            "pm10_change_per_day": "pm10_change_per_day",
        },
    },
    "serving_dust_event_daily": {
        "view": "dust_aoi_daily",
        "table": "source_dust_daily",
        "rolling": {"aod_mean": (7,), "wind_speed_mean": (7,)},
        "fields": (
            "aod_mean", "aod_max", "uv_aerosol_index_mean",
            "wind_speed_mean", "wind_dir_dominant", "corridor_aod_max",
            "valid_fraction", "dust_severity_band", "dust_flag", "transport_flag",
            "aod_7d_mean", "aod_change_per_day", "wind_speed_change_per_day",
        ),
        "mapping": {
            "aod_mean": "aod_mean", "aod_max": "aod_max",
            "uv_aerosol_index_mean": "uv_aerosol_index_mean",
            "wind_speed_mean": "wind_speed_mean",
            "wind_dir_dominant": "wind_dir_dominant",
            "corridor_aod_max": "corridor_aod_max",
            "valid_fraction": "valid_fraction",
            "dust_severity_band": "dust_severity_band",
            "dust_flag": "dust_flag", "transport_flag": "transport_flag",
            "aod_7d_mean": "aod_7d_mean",
            "aod_change_per_day": "aod_change_per_day",
            "wind_speed_change_per_day": "wind_speed_change_per_day",
        },
    },
    "serving_climate_indicator_daily": {
        "view": "climate_indicator_aoi_daily",
        "table": "source_climate_indicator_daily",
        "rolling": {"lst_anomaly_c": (7,), "ndvi_mean": (30,)},
        "fields": (
            "lst_c", "lst_anomaly_c", "sst_c", "sst_anomaly_c",
            "ndvi_mean", "evi_mean", "ndwi_mean", "tree_cover_loss_ha",
            "desertification_proxy", "lst_anomaly_band", "warming_flag",
            "desertification_flag", "lst_anomaly_7d_mean",
            "lst_anomaly_change_per_day", "ndvi_30d_mean",
            "ndvi_change_per_day",
        ),
        "mapping": {
            "lst_c": "lst_c", "lst_anomaly_c": "lst_anomaly_c",
            "sst_c": "sst_c", "sst_anomaly_c": "sst_anomaly_c",
            "ndvi_mean": "ndvi_mean", "evi_mean": "evi_mean",
            "ndwi_mean": "ndwi_mean",
            "tree_cover_loss_ha": "tree_cover_loss_ha",
            "desertification_proxy": "desertification_proxy",
            "lst_anomaly_band": "lst_anomaly_band",
            "warming_flag": "warming_flag",
            "desertification_flag": "desertification_flag",
            "lst_anomaly_7d_mean": "lst_anomaly_7d_mean",
            "lst_anomaly_change_per_day": "lst_anomaly_change_per_day",
            "ndvi_30d_mean": "ndvi_30d_mean",
            "ndvi_change_per_day": "ndvi_change_per_day",
        },
    },
    "serving_vegetation_health_daily": {
        "view": "vegetation_health_aoi_daily",
        "table": "source_vegetation_health_daily",
        "rolling": {"ndvi_mean": (30,)},
        "fields": (
            "ndvi_mean", "ndvi_max", "evi_mean", "ndvi_trend_30d",
            "valid_pixel_fraction", "ndvi_health_band", "crop_stress_flag",
            "ndvi_30d_mean", "ndvi_change_per_day",
        ),
        "mapping": {
            "ndvi_mean": "ndvi_mean", "ndvi_max": "ndvi_max",
            "evi_mean": "evi_mean", "ndvi_trend_30d": "ndvi_trend_30d",
            "valid_pixel_fraction": "valid_pixel_fraction",
            "ndvi_health_band": "ndvi_health_band",
            "crop_stress_flag": "crop_stress_flag",
            "ndvi_30d_mean": "ndvi_30d_mean",
            "ndvi_change_per_day": "ndvi_change_per_day",
        },
    },
}


def _serving_db_path() -> Path:
    return Path(
        os.environ.get(
            "FEATURE_STORE_SERVING_DB",
            str(Path(__file__).parents[2] / "serving" / "dbt" / "serving.duckdb"),
        )
    )


def _feature_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value)
    if len(text) == 8 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d").date()
    return date.fromisoformat(text[:10])


def _sync_climate_product(
    product_name: str,
    product: dict[str, Any],
    serving_rows: list[dict[str, Any]],
    database_path: Path,
) -> GoldSyncResult:
    view_name = product["view"]
    table_name = product["table"]
    if not serving_rows:
        return GoldSyncResult(
            source=product_name,
            status="no_data",
            rows_written=0,
            detail="The Phase 11b serving product has no rows.",
        )
    normalized_rows = []
    seen: set[tuple[str, date]] = set()
    for source_row in serving_rows:
        aoi_key = source_row.get("aoi_key")
        raw_date = source_row.get("date_key")
        if aoi_key in (None, "") or raw_date is None:
            raise ValueError(f"{product_name} contains a null AOI/date key.")
        feature_date = _feature_date(raw_date)
        grain = (str(aoi_key), feature_date)
        if grain in seen:
            raise ValueError(f"{product_name} contains duplicate AOI/date grain {grain!r}.")
        seen.add(grain)
        normalized_rows.append(
            {
                **source_row,
                "aoi_key": str(aoi_key),
                "date_key": feature_date.isoformat(),
                "event_timestamp": datetime.combine(
                    feature_date, time.min, timezone.utc
                ),
            }
        )

    enriched_rows = add_temporal_features(
        normalized_rows,
        rolling_windows=product["rolling"],
    )
    quality_errors = validate_climate_feature_rows(view_name, enriched_rows)
    if quality_errors:
        return GoldSyncResult(
            source=product_name,
            status="quality_failed",
            rows_written=0,
            detail="; ".join(quality_errors),
        )

    readiness_status = FEATURE_READINESS[view_name].status
    source_published_at = datetime.fromtimestamp(
        database_path.stat().st_mtime,
        timezone.utc,
    ).isoformat()
    source_reference = f"duckdb:///{database_path.as_posix()}#serving.{product_name}"
    columns = [
        "aoi_key",
        "event_timestamp",
        "created_timestamp",
        "feature_date",
        *product["fields"],
        "days_since_previous_observation",
        "source_published_at",
        "data_nature",
        "readiness_status",
        "source_reference",
    ]
    values = [
        (
            row["aoi_key"],
            row["event_timestamp"],
            row["event_timestamp"],
            row["date_key"],
            *(row.get(product["mapping"].get(field, field)) for field in product["fields"]),
            row.get("days_since_previous_observation"),
            source_published_at,
            "phase_11b_serving_product",
            readiness_status,
            source_reference,
        )
        for row in enriched_rows
    ]
    if values:
        placeholders = ", ".join(["%s"] * len(columns))
        update_columns = [column for column in columns if column not in {"aoi_key", "event_timestamp"}]
        updates = ", ".join(
            f"{column} = EXCLUDED.{column}" for column in update_columns
        )
        with connect() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    f"""
                    INSERT INTO feast.{table_name} ({", ".join(columns)})
                    VALUES ({placeholders})
                    ON CONFLICT (aoi_key, event_timestamp) DO UPDATE SET {updates}
                    """,
                    values,
                )

    return GoldSyncResult(
        source=product_name,
        status=readiness_status if values else "no_data",
        rows_written=len(values),
        detail=(
            "Synchronized from the Phase 11b serving product; feature readiness remains "
            f"{readiness_status}."
            if values
            else "The Phase 11b serving product has no rows."
        ),
    )


def sync_climate_serving_products() -> list[GoldSyncResult]:
    database_path = _serving_db_path()
    if not database_path.is_file():
        return [
            GoldSyncResult(
                source=name,
                status="blocked",
                rows_written=0,
                detail=f"Serving DuckDB product file is unavailable: {database_path}",
            )
            for name in _CLIMATE_PRODUCTS
        ]

    import duckdb

    database = duckdb.connect(str(database_path), read_only=True)
    try:
        catalog = database.execute("SELECT current_database()").fetchone()[0]
        available = {
            row[0]
            for row in database.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'serving'
                """
            ).fetchall()
        }
        results = []
        for product_name, product in _CLIMATE_PRODUCTS.items():
            if product_name not in available:
                results.append(
                    GoldSyncResult(
                        source=product_name,
                        status="no_data",
                        rows_written=0,
                        detail="The Phase 11b serving product table is not present.",
                    )
                )
                continue
            cursor = database.execute(
                f'SELECT * FROM "{catalog}".serving."{product_name}"'
            )
            names = [column[0] for column in cursor.description]
            source_rows = [
                dict(zip(names, values, strict=True))
                for values in cursor.fetchall()
            ]
            results.append(
                _sync_climate_product(
                    product_name,
                    product,
                    source_rows,
                    database_path,
                )
            )
        return results
    finally:
        database.close()


def sync_enabled_gold_sources() -> list[dict[str, object]]:
    return [
        asdict(result)
        for result in [
            sync_scene_catalog(),
            *sync_climate_serving_products(),
        ]
    ]
