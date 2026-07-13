"""Climate Bronze -> Silver transforms (Phase 9b).

Companion to :mod:`transformation.batch.bronze_to_silver` for the atmospheric
domain. Each ``silver_*`` function takes *unwrapped* Bronze records and returns a
:class:`~transformation.batch.bronze_to_silver.SilverResult` with conformed rows
and quarantined rows, applying the shared cleaners in
:mod:`transformation.cleaning.climate` plus dedup by natural key.

Silver entities produced (docs/data-modeling/climate/02-silver-entities.md):

* ``obs_air_quality``  — OpenAQ surface pollutants (station -> AOI tagged here)
* ``obs_aerosol``      — MODIS/VIIRS AOD per AOI per day
* ``obs_atmos_column`` — TROPOMI trace-gas columns per AOI per day

``run_spark`` reuses the same cleaners as ``mapInPandas`` logic so the cluster
and offline paths share one definition of "clean" (existing convention).
"""

from __future__ import annotations

from typing import Any, Callable

from transformation.batch.bronze_to_silver import SilverResult, _quarantine
from transformation.cleaning.cleaning_rules import CleanResult, deduplicate
from transformation.cleaning.climate.aerosol import clean_aerosol
from transformation.cleaning.climate.air_quality import clean_air_quality
from transformation.cleaning.climate.atmos_column import clean_atmos_column
from transformation.geospatial.spatial_transform import assign_aoi


def _apply(records: list[dict[str, Any]], cleaner: Callable[[dict[str, Any]], CleanResult],
           *, entity: str, key_fields: list[str]) -> SilverResult:
    """Clean, quarantine failures, then dedup latest-by-event-time per key."""
    kept: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    for rec in records:
        result = cleaner(rec)
        if result.rejected or result.record is None:
            quarantine.append(_quarantine(rec, result.reasons, entity))
        else:
            kept.append(result.record)
    deduped = deduplicate(kept, key_fields=key_fields, order_field="event_ts")
    return SilverResult(entity=entity, rows=deduped, quarantine=quarantine)


def _tag_aoi(rows: list[dict[str, Any]], aois: list[dict[str, Any]]) -> None:
    """Assign ``aoi_id`` by point-in-polygon, keeping the Bronze value as fallback.

    Reuses the shared geospatial point-in-polygon engine (``assign_aoi``). The
    first AOI whose footprint contains the station wins; a station outside every
    footprint keeps its Bronze-stamped request AOI (nullable).
    """
    if not aois:
        return
    for row in rows:
        matched = assign_aoi(row.get("latitude"), row.get("longitude"), aois)
        if matched:
            row["aoi_id"] = matched[0]


# --- obs_air_quality (OpenAQ) ----------------------------------------------

def silver_air_quality(records: list[dict[str, Any]],
                       aois: list[dict[str, Any]] | None = None) -> SilverResult:
    """Conform OpenAQ readings; tag stations to AOIs via point-in-polygon."""
    result = _apply(records, clean_air_quality, entity="silver_air_quality",
                    key_fields=["air_quality_key"])
    _tag_aoi(result.rows, aois or [])
    return result


# --- obs_aerosol (MODIS/VIIRS AOD) -----------------------------------------

def silver_aerosol(records: list[dict[str, Any]]) -> SilverResult:
    """Conform MODIS/VIIRS AOD buckets (AOI already carried from Bronze)."""
    return _apply(records, clean_aerosol, entity="silver_aerosol",
                  key_fields=["aerosol_key"])


# --- obs_atmos_column (TROPOMI) --------------------------------------------

def silver_atmos_column(records: list[dict[str, Any]]) -> SilverResult:
    """Conform TROPOMI trace-gas column buckets (AOI already carried from Bronze)."""
    return _apply(records, clean_atmos_column, entity="silver_atmos_column",
                  key_fields=["atmos_key"])


# --- Spark entrypoint (requires infrastructure) -----------------------------

def _silver_spark_schema(entity: str):  # pragma: no cover - needs Spark
    """Explicit ``StructType`` per climate Silver entity.

    Climate rows routinely carry all-null columns (e.g. no ``angstrom_exponent``,
    no ``uv_aerosol_index`` before the denormalization join), which breaks
    ``createDataFrame`` type inference. Declaring the contract makes the write
    deterministic and lets an *empty* source still land a readable Parquet.
    """
    from pyspark.sql.types import (
        DoubleType, StringType, StructField, StructType,
    )

    def _s(name: str) -> StructField:
        return StructField(name, StringType(), True)

    def _d(name: str) -> StructField:
        return StructField(name, DoubleType(), True)

    from pyspark.sql.types import BooleanType

    def _b(name: str) -> StructField:
        return StructField(name, BooleanType(), True)

    schemas = {
        "air_quality": StructType([
            _s("air_quality_key"), _s("event_ts"), _s("stat_date"),
            _s("location_id"), _s("pollutant_code"), _d("value_std"),
            _d("value_raw"), _s("unit_raw"), _d("latitude"), _d("longitude"),
            _s("geo_key"), _s("aoi_id"), _s("quality_flag"), _s("source"),
            _s("_ingest_id"), _s("_batch_id"),
        ]),
        "aerosol": StructType([
            _s("aerosol_key"), _s("stat_date"), _s("event_ts"), _s("aoi_id"),
            _s("geo_key"), _s("bbox"), _s("sensor"), _d("aod_550nm"),
            _d("angstrom_exponent"), _d("uv_aerosol_index"),
            _b("bright_surface_flag"), _d("valid_fraction"), _s("quality_flag"),
            _s("source"), _s("_ingest_id"), _s("_batch_id"),
        ]),
        "atmos_column": StructType([
            _s("atmos_key"), _s("stat_date"), _s("event_ts"), _s("aoi_id"),
            _s("geo_key"), _s("bbox"), _s("gas_code"), _d("mean"), _d("min"),
            _d("max"), _d("stddev"), _s("unit_std"), _d("valid_pixel_fraction"),
            _s("quality_flag"), _s("source"), _s("_ingest_id"), _s("_batch_id"),
        ]),
    }
    return schemas.get(entity)


def run_spark(entity: str) -> None:  # pragma: no cover - needs Spark/MinIO
    """Read Bronze, apply the matching climate Silver transform, write Parquet."""
    from pyspark.sql.utils import AnalysisException

    from transformation.batch.gold_lakehouse import load_aoi_reference
    from transformation.common.io import unwrap_bronze
    from transformation.common.spark import build_spark_session, coerce_rows_to_schema
    from transformation.config.settings import settings

    transforms: dict[str, tuple[list[str], Callable[..., SilverResult]]] = {
        "air_quality": (["OPENAQ"], silver_air_quality),
        "aerosol": (["MODIS_AOD"], silver_aerosol),
        "atmos_column": (["TROPOMI"], silver_atmos_column),
    }
    if entity not in transforms:
        raise ValueError(f"unknown climate entity: {entity}")
    datasets, fn = transforms[entity]

    spark = build_spark_session(f"silver-{entity}")
    silver_path = settings.lake.path("silver", f"silver_{entity}")

    records: list[dict[str, Any]] = []
    for dataset in datasets:
        try:
            bronze = spark.read.json(settings.lake.path("bronze", dataset))
        except AnalysisException:
            print(f"[run_silver] bronze source not found, skipping: {dataset}")
            continue
        records.extend(r.asDict(recursive=True) for r in bronze.collect())

    unwrapped = [unwrap_bronze(r) for r in records]
    if entity == "air_quality":
        result = fn(unwrapped, load_aoi_reference())
    else:
        result = fn(unwrapped)

    schema = _silver_spark_schema(entity)
    frame = spark.createDataFrame(coerce_rows_to_schema(result.rows, schema), schema=schema)
    frame.write.mode("overwrite").parquet(silver_path)
    print(f"[run_silver] wrote silver_{entity}: {len(result.rows)} row(s) -> {silver_path}")
    spark.stop()
