#!/usr/bin/env bash
# ============================================================================
# run_pipeline.sh — one-command Bronze -> Silver -> Gold inside spark-master
# ----------------------------------------------------------------------------
# Designed to be exec'd in the (hardened) spark-master container, which already
# carries the code mount, dbt-duckdb, the cached Ivy jars, and the MinIO/Kafka
# wiring via environment. After a `docker compose up`, the whole batch path is:
#
#   docker exec -u root space-platform-spark-master-1 \
#       bash /opt/spark/work-dir/transformation/scripts/run_pipeline.sh
#
# Bronze data lives in the MinIO volume, so it survives stop/start and even
# down/up (without -v); re-seed only after a `down -v` / reset (see --seed note).
# ============================================================================
set -euo pipefail

WORKDIR=/opt/spark/work-dir
SUBMIT_PKGS="org.apache.hadoop:hadoop-aws:3.3.4"
SPARK_SUBMIT=(
  /opt/spark/bin/spark-submit
  --packages "$SUBMIT_PKGS"
  --conf spark.jars.ivy=/tmp/.ivy2
  --conf spark.sql.extensions=            # spark-defaults loads an absent Iceberg ext jar
  --conf spark.driver.host=localhost
  --conf spark.driver.bindAddress=127.0.0.1
)

cd "$WORKDIR"

echo "==================== Bronze -> Silver (Spark + S3A) ===================="
# Simulation-track entities (fully typed) + MVP Earth-observation entities.
# Run one entity per spark-submit: a single local JVM handles them serially and
# an absent Bronze source is skipped inside run_spark rather than aborting.
for entity in telemetry orbit space_weather fire vessel scene index; do
  echo "--> silver: $entity"
  "${SPARK_SUBMIT[@]}" transformation/scripts/run_silver.py "$entity"
done

echo "==================== Silver -> Gold (Spark -> s3://gold) ==============="
# Materialises every business-ready mart (sim + MVP EO) to s3://gold/<table>/
# Parquet — the serving layer's only source. Reuses the tested pure-Python Gold
# rules (point-in-polygon AOI attribution can't be expressed in dbt SQL).
"${SPARK_SUBMIT[@]}" transformation/scripts/run_gold.py

echo "==================== Silver -> Gold (dbt-duckdb demonstrator) =========="
# Analytics-engineering demonstrator: the sim-track Gold also materialises to a
# local DuckDB warehouse for interactive querying (post-MVP, not serving input).
cd "$WORKDIR/transformation/dbt"
dbt deps
dbt run
dbt test

echo "==================== DONE ==============================================="
echo "Gold lakehouse: s3://gold/<table>/*.parquet (serving source)"
echo "Gold warehouse: ${DBT_DUCKDB_PATH:-$WORKDIR/transformation/dbt/space.duckdb}"
