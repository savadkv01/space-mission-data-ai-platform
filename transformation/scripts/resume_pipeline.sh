#!/usr/bin/env bash
# ============================================================================
# resume_pipeline.sh — resume run_pipeline.sh from the climate Silver step
# onward (aerosol/atmos_column -> Gold -> dbt demonstrator). Used when a prior
# run_pipeline.sh invocation completed the sim + MVP-EO + air_quality Silver
# jobs but was interrupted (e.g. OOM on an oversized Bronze source) before
# finishing. Safe to re-run; each Silver/Gold job overwrites its own output.
# ============================================================================
set -euo pipefail

WORKDIR=/opt/spark/work-dir
SUBMIT_PKGS="org.apache.hadoop:hadoop-aws:3.3.4"
SPARK_SUBMIT=(
  /opt/spark/bin/spark-submit
  --packages "$SUBMIT_PKGS"
  --conf spark.jars.ivy=/tmp/.ivy2
  --conf spark.sql.extensions=
  --conf spark.driver.host=localhost
  --conf spark.driver.bindAddress=127.0.0.1
)

cd "$WORKDIR"

for entity in aerosol atmos_column; do
  echo "--> climate silver: $entity"
  "${SPARK_SUBMIT[@]}" transformation/scripts/run_climate_silver.py "$entity"
done

echo "==================== Silver -> Gold (Spark -> s3://gold) ==============="
"${SPARK_SUBMIT[@]}" transformation/scripts/run_gold.py

echo "==================== Silver -> Gold (dbt-duckdb demonstrator) =========="
cd "$WORKDIR/transformation/dbt"
dbt deps
dbt run
dbt test

echo "==================== RESUME DONE ========================================="
