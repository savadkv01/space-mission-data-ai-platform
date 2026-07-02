"""Silver -> Gold lakehouse writer (Task 9 infra path).

Materialises every business-ready Gold mart to ``s3://gold/<table>/`` as Parquet
— the exact layout the **serving** layer's dbt sources resolve
(``s3://gold/{name}/*.parquet``). It deliberately reuses the pure-Python
:mod:`transformation.batch.silver_to_gold` rules rather than reimplementing them
in SQL, because the Earth-observation marts (wildfire / flood / validation) need
point-in-polygon AOI attribution that dbt-duckdb cannot express (ADR-SV-01).

Data flow
---------
1. Read each ``silver_<entity>`` Parquet partition from ``s3://silver`` (any
   absent entity is treated as empty so a partial pipeline still produces Gold).
2. Load the Copernicus-EMS AOI reference *seed* shipped in-repo
   (``transformation/seeds/aoi_reference.geojson``) — reference/master data that
   also serves as validation ground truth.
3. Run the tested Gold aggregations (sim + MVP EO).
4. Write all ten Gold marts with an **explicit** Spark schema so all-null
   columns never break ``createDataFrame`` and empty marts still land a readable
   (0-row) Parquet, keeping the serving contract stable.

Run inside spark-master:

    spark-submit --packages org.apache.hadoop:hadoop-aws:3.3.4 \
        transformation/scripts/run_gold.py
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable

from transformation.batch.bronze_to_silver import (
    _expand_feature_collections, clean_ems_aoi,
)
from transformation.batch.silver_to_gold import (
    gold_aoi_validation, gold_earth_observation, gold_flood_aoi,
    gold_launch_performance, gold_satellite_health, gold_scene_catalog,
    gold_space_weather_impact, gold_vessel_activity, gold_wildfire_aoi,
)

#: Default seed location inside the spark-master code mount.
_DEFAULT_SEED = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "seeds", "aoi_reference.geojson",
)


def load_aoi_reference(seed_path: str | None = None) -> list[dict[str, Any]]:
    """Parse the AOI reference seed into Silver ``ref_aoi`` rows.

    Each row keeps its ``bbox`` + ``polygons`` in memory so the EO Gold rules can
    run point-in-polygon attribution. Returns ``[]`` if the seed is absent.
    """
    path = seed_path or os.environ.get("AOI_SEED_PATH") or _DEFAULT_SEED
    if not os.path.exists(path):
        print(f"[run_gold] AOI seed not found, EO AOI marts will be empty: {path}")
        return []
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    rows: list[dict[str, Any]] = []
    for feature in _expand_feature_collections([payload]):
        result = clean_ems_aoi(feature)
        if result.record is not None:
            rows.append(result.record)
    print(f"[run_gold] loaded {len(rows)} AOI reference footprint(s) from seed")
    return rows


def _ref_aoi_row(aoi: dict[str, Any]) -> dict[str, Any]:
    """Flatten an in-memory AOI into the serving ``ref_aoi`` dimension row."""
    bbox = aoi.get("bbox") or []
    bbox_str = ",".join(str(v) for v in bbox) if bbox else None
    return {
        "aoi_key": aoi.get("aoi_key"),
        "aoi_name": aoi.get("aoi_name"),
        "event_type": aoi.get("event_type"),
        "event_date": (aoi.get("event_date") or "")[:10] or None,
        "area_km2": aoi.get("area_km2"),
        "geo_key": aoi.get("geo_key"),
        "bbox": bbox_str,
    }


def build_marts(silver: dict[str, list[dict[str, Any]]],
                aois: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Compute every Gold mart from Silver rows + the AOI reference (pure Python)."""
    fire = silver.get("fire", [])
    index = silver.get("index", [])
    wildfire = gold_wildfire_aoi(fire, aois)
    flood = gold_flood_aoi(index, aois)
    return {
        # --- MVP Earth-observation marts ---
        "kpi_wildfire_aoi_daily": wildfire,
        "kpi_flood_aoi_daily": flood,
        "fact_vessel_activity": gold_vessel_activity(silver.get("vessel", [])),
        "fact_scene_catalog": gold_scene_catalog(silver.get("scene", [])),
        "kpi_eo_daily": gold_earth_observation(fire),
        "kpi_aoi_validation": gold_aoi_validation(aois, wildfire, flood),
        "ref_aoi": [_ref_aoi_row(a) for a in aois],
        # --- Simulation-track marts (post-MVP demonstrator, ADR-09) ---
        "fact_sat_health": gold_satellite_health(silver.get("telemetry", [])),
        "kpi_launch_monthly": gold_launch_performance(silver.get("launch", [])),
        "fact_weather_impact": gold_space_weather_impact(
            silver.get("space_weather", []), silver.get("telemetry", [])),
    }


def _gold_spark_schemas():  # pragma: no cover - needs Spark
    """Explicit ``StructType`` per Gold mart (all marts are flat)."""
    from pyspark.sql.types import (
        BooleanType, DoubleType, LongType, StringType, StructField, StructType,
    )

    def _s(n: str) -> StructField:
        return StructField(n, StringType(), True)

    def _d(n: str) -> StructField:
        return StructField(n, DoubleType(), True)

    def _l(n: str) -> StructField:
        return StructField(n, LongType(), True)

    def _b(n: str) -> StructField:
        return StructField(n, BooleanType(), True)

    return {
        "kpi_wildfire_aoi_daily": StructType([
            _s("aoi_key"), _s("date_key"), _l("detections"), _d("mean_frp"),
            _d("max_frp"),
        ]),
        "kpi_flood_aoi_daily": StructType([
            _s("aoi_key"), _s("date_key"), _d("ndwi_mean"), _d("ndwi_max"),
            _d("valid_pixel_fraction"), _b("flood_flag"),
        ]),
        "fact_vessel_activity": StructType([
            _s("vessel_key"), _s("date_key"), _l("transmissions"), _s("flag"),
            _s("vessel_type"), _b("suspicious_flag"), _l("active_span_days"),
        ]),
        "fact_scene_catalog": StructType([
            _s("scene_key"), _s("date_key"), _s("collection"), _s("provider"),
            _s("platform"), _s("geo_key"), _d("cloud_cover"),
            _d("completeness_score"), _b("is_searchable"),
        ]),
        "kpi_eo_daily": StructType([
            _s("geo_key"), _s("date_key"), _l("detections"), _d("mean_frp"),
            _d("median_frp"), _d("max_frp"),
        ]),
        "kpi_aoi_validation": StructType([
            _s("aoi_key"), _s("event_type"), _s("event_date"), _d("area_km2"),
            _l("evidence_days"), _b("corroborated"),
        ]),
        "ref_aoi": StructType([
            _s("aoi_key"), _s("aoi_name"), _s("event_type"), _s("event_date"),
            _d("area_km2"), _s("geo_key"), _s("bbox"),
        ]),
        "fact_sat_health": StructType([
            _s("sat_key"), _s("date_key"), _l("samples"), _d("health_score"),
            _l("anomaly_samples"), _l("labelled_anomalies"), _d("anomaly_density"),
            _d("battery_voltage_drift"),
        ]),
        "kpi_launch_monthly": StructType([
            _s("provider_key"), _s("month_key"), _l("launches"), _l("successes"),
            _d("success_rate"), _l("cadence_per_month"), _d("mean_delay_days"),
        ]),
        "fact_weather_impact": StructType([
            _s("date_key"), _d("max_kp_index"), _d("mean_kp_index"),
            _l("storm_events"), _l("telemetry_samples"), _l("anomaly_samples"),
            _d("anomaly_rate"),
        ]),
    }


def run_gold_spark(seed_path: str | None = None) -> None:  # pragma: no cover - needs Spark
    """Read Silver Parquet, build all Gold marts, write them to ``s3://gold``."""
    from pyspark.sql.utils import AnalysisException

    from transformation.common.spark import build_spark_session, coerce_rows_to_schema
    from transformation.config.settings import settings

    spark = build_spark_session("gold-lakehouse")

    def _read_silver(entity: str) -> list[dict[str, Any]]:
        path = settings.lake.path("silver", f"silver_{entity}")
        try:
            frame = spark.read.parquet(path)
        except AnalysisException:
            print(f"[run_gold] silver source not found, skipping: {entity}")
            return []
        rows = [row.asDict(recursive=True) for row in frame.collect()]
        print(f"[run_gold] read silver_{entity}: {len(rows)} row(s)")
        return rows

    silver = {
        entity: _read_silver(entity)
        for entity in ("telemetry", "space_weather", "fire", "vessel", "scene", "index")
    }
    aois = load_aoi_reference(seed_path)
    marts = build_marts(silver, aois)

    schemas = _gold_spark_schemas()
    for table, rows in marts.items():
        gold_path = settings.lake.path("gold", table)
        schema = schemas[table]
        frame = spark.createDataFrame(coerce_rows_to_schema(rows, schema), schema=schema)
        frame.write.mode("overwrite").parquet(gold_path)
        print(f"[run_gold] wrote gold/{table}: {len(rows)} row(s) -> {gold_path}")

    spark.stop()


if __name__ == "__main__":  # pragma: no cover
    run_gold_spark()
