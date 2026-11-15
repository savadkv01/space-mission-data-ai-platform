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

from typing import Any, Callable, Iterable

from transformation.batch.bronze_to_silver import SilverResult, _quarantine
from transformation.cleaning.cleaning_rules import CleanResult, natural_key
from transformation.cleaning.climate.aerosol import clean_aerosol
from transformation.cleaning.climate.air_quality import clean_air_quality, flag_sensor_anomalies
from transformation.cleaning.climate.atmos_column import clean_atmos_column
from transformation.cleaning.climate.wind import clean_power_wind
from transformation.geospatial.aoi_geometry import (
    aoi_bbox_index,
    bbox_geometry_reason,
    point_geometry_reason,
)
from transformation.geospatial.spatial_transform import attribute_point, reporting_aois


def _apply(records: Iterable[dict[str, Any]],
           cleaner: Callable[[dict[str, Any]], CleanResult],
           *, entity: str, key_fields: list[str],
           precedence: Callable[[dict[str, Any]], Any] | None = None,
           geometry_reason: Callable[[dict[str, Any]], str | None] | None = None,
           ) -> SilverResult:
    """Clean, quarantine failures, then keep the latest row per natural key.

    Streams ``records`` once and deduplicates incrementally, so memory grows
    with unique keys, not with raw Bronze re-pulls (rolling windows re-land the
    same readings every run). The latest ``event_ts`` wins; ``precedence``
    breaks event-time ties (higher wins), then the last seen wins — the same
    result as sorting by precedence and calling ``deduplicate``.
    ``geometry_reason`` quarantines Bronze records whose AOI geometry is retired
    or superseded (ADR-12) before cleaning.
    """
    best: dict[tuple, tuple[tuple[str, Any], dict[str, Any]]] = {}
    quarantine: list[dict[str, Any]] = []
    for rec in records:
        reason = geometry_reason(rec) if geometry_reason else None
        if reason:
            quarantine.append(_quarantine(rec, [reason], entity))
            continue
        result = cleaner(rec)
        if result.rejected or result.record is None:
            quarantine.append(_quarantine(rec, result.reasons, entity))
            continue
        row = result.record
        rank = (str(row.get("event_ts", "")), precedence(row) if precedence else 0)
        key = natural_key(row, key_fields)
        current = best.get(key)
        if current is None or rank >= current[0]:
            best[key] = (rank, row)
    return SilverResult(entity=entity, rows=[row for _, row in best.values()],
                        quarantine=quarantine)


def _box_guard(aois: list[dict[str, Any]] | None) -> Callable[[dict[str, Any]], str | None]:
    index = aoi_bbox_index(aois)
    return lambda rec: bbox_geometry_reason(rec.get("aoi_id"), rec.get("bbox"), index)


def _tag_aoi(rows: list[dict[str, Any]], aois: list[dict[str, Any]]) -> None:
    """Assign ``aoi_id`` to the station's reporting AOI by point-in-polygon.

    Only rollup-eligible AOIs are considered (an event overlay such as an EMS
    footprint must not capture the stations of the reporting unit beneath it).
    A station outside every reporting AOI keeps its Bronze request AOI only if
    that AOI is still a reporting unit; otherwise it is left unattributed.
    """
    if not aois:
        return
    reporting = reporting_aois(aois)
    reporting_keys = {a.get("aoi_key") for a in reporting}
    for row in rows:
        matched, _ = attribute_point(row.get("latitude"), row.get("longitude"), reporting)
        if matched:
            row["aoi_id"] = matched
        elif row.get("aoi_id") not in reporting_keys:
            row["aoi_id"] = None


# --- obs_air_quality (OpenAQ) ----------------------------------------------

def silver_air_quality(records: list[dict[str, Any]],
                       aois: list[dict[str, Any]] | None = None) -> SilverResult:
    """Conform OpenAQ readings, flag implausible sensor series, tag stations to AOIs."""
    result = _apply(records, clean_air_quality, entity="silver_air_quality",
                    key_fields=["air_quality_key"])
    flag_sensor_anomalies(result.rows)
    _tag_aoi(result.rows, aois or [])
    return result


# --- obs_aerosol (MODIS/VIIRS AOD) -----------------------------------------

def silver_aerosol(records: list[dict[str, Any]],
                   aois: list[dict[str, Any]] | None = None) -> SilverResult:
    """Conform MODIS/VIIRS AOD buckets (AOI already carried from Bronze).

    On a key collision the QA-masked record with aerosol-model shares wins.
    """
    return _apply(records, clean_aerosol, entity="silver_aerosol",
                  key_fields=["aerosol_key"],
                  precedence=lambda r: (int(r.get("qa_mask") is not None),
                                        int(r.get("smoke_fraction") is not None
                                            or r.get("dust_fraction") is not None)),
                  geometry_reason=_box_guard(aois))


# --- obs_atmos_column (TROPOMI) --------------------------------------------

def silver_atmos_column(records: list[dict[str, Any]],
                        aois: list[dict[str, Any]] | None = None) -> SilverResult:
    """Conform TROPOMI trace-gas column buckets (AOI already carried from Bronze)."""
    return _apply(records, clean_atmos_column, entity="silver_atmos_column",
                  key_fields=["atmos_key"], geometry_reason=_box_guard(aois))


# --- obs_wind (NASA POWER) --------------------------------------------------

def silver_wind(records: list[dict[str, Any]],
                aois: list[dict[str, Any]] | None = None) -> SilverResult:
    """Conform daily NASA POWER wind observations at AOI representative points."""
    wind_records = [
        row for row in records
        if str(row.get("parameter") or "").upper() in {"WS2M", "WD2M"}
    ]
    index = aoi_bbox_index(aois)
    return _apply(
        wind_records,
        clean_power_wind,
        entity="silver_wind",
        key_fields=["aoi_id", "stat_date", "parameter"],
        precedence=lambda r: int(r.get("time_standard") == "UTC"),
        geometry_reason=lambda rec: point_geometry_reason(
            rec.get("aoi_id"), rec.get("latitude"), rec.get("longitude"), index),
    )


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
            _s("geo_key"), _s("aoi_id"), _s("quality_flag"), _s("qa_reason"), _s("source"),
            _s("_ingest_id"), _s("_batch_id"),
        ]),
        "aerosol": StructType([
            _s("aerosol_key"), _s("stat_date"), _s("event_ts"), _s("aoi_id"),
            _s("geo_key"), _s("bbox"), _s("sensor"), _d("aod_550nm"),
            _d("angstrom_exponent"), _d("uv_aerosol_index"),
            _b("bright_surface_flag"), _d("valid_fraction"), _s("quality_flag"),
            _s("qa_mask"), _d("smoke_fraction"), _d("dust_fraction"), _s("aerosol_model"),
            _s("source"), _s("_ingest_id"), _s("_batch_id"),
        ]),
        "atmos_column": StructType([
            _s("atmos_key"), _s("stat_date"), _s("event_ts"), _s("aoi_id"),
            _s("geo_key"), _s("bbox"), _s("gas_code"), _d("mean"), _d("min"),
            _d("max"), _d("stddev"), _s("unit_std"), _d("valid_pixel_fraction"),
            _s("quality_flag"), _s("source"), _s("_ingest_id"), _s("_batch_id"),
        ]),
        "wind": StructType([
            _s("wind_key"), _s("event_ts"), _s("stat_date"), _s("aoi_id"),
            _s("parameter"), _d("value_std"), _s("unit_std"), _d("latitude"),
            _d("longitude"), _s("time_standard"), _s("quality_flag"), _s("source"),
            _s("_ingest_id"), _s("_batch_id"),
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
        "wind": (["POWER"], silver_wind),
    }
    if entity not in transforms:
        raise ValueError(f"unknown climate entity: {entity}")
    datasets, fn = transforms[entity]

    spark = build_spark_session(f"silver-{entity}")
    silver_path = settings.lake.path("silver", f"silver_{entity}")

    frames = []
    for dataset in datasets:
        try:
            frames.append(spark.read.json(settings.lake.path("bronze", dataset)))
        except AnalysisException:
            print(f"[run_silver] bronze source not found, skipping: {dataset}")
            continue

    def _bronze_records():
        # Stream partition by partition instead of collect(): Bronze grows with
        # every rolling-window re-pull, and a full collect() of OpenAQ Bronze
        # (~290k rows) exceeded the 2 GiB spark-master container (exit 137).
        for frame in frames:
            for row in frame.toLocalIterator(prefetchPartitions=False):
                yield unwrap_bronze(row.asDict(recursive=True))

    # Every climate entity needs the AOI seed: station tagging for air quality,
    # the retired/superseded geometry guard for the request-based entities.
    result = fn(_bronze_records(), load_aoi_reference())

    schema = _silver_spark_schema(entity)
    frame = spark.createDataFrame(coerce_rows_to_schema(result.rows, schema), schema=schema)
    frame.write.mode("overwrite").parquet(silver_path)
    print(f"[run_silver] wrote silver_{entity}: {len(result.rows)} row(s) -> {silver_path}")
    spark.stop()
