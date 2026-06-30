# syntax=docker/dockerfile:1
# ============================================================================
# Spark 3.5.1 + dbt-duckdb transformation runner
# ----------------------------------------------------------------------------
# Extends the stock Spark image so the SAME container runs both halves of the
# transformation layer with no runtime installs:
#   * Bronze -> Silver  (PySpark + hadoop-aws/S3A, already in the base image)
#   * Silver -> Gold    (dbt-duckdb reading Silver Parquet from MinIO via httpfs)
#
# Built automatically by docker-compose.processing.yml (spark-master service);
# the image is cached, so a cold `docker compose up` "just works" — the ~6 min
# dbt install happens once at build time, never per run.
# Repo code is bind-mounted at runtime (not copied), so edits need no rebuild.
# ============================================================================
FROM apache/spark:3.5.1

USER root

# dbt-duckdb materialises the Gold marts into an in-process DuckDB warehouse.
# Pinned for reproducibility; matches transformation/requirements-spark.txt.
RUN python3 -m pip install --no-cache-dir \
        "dbt-duckdb~=1.7.0" \
        "duckdb>=0.9,<0.11" \
    && dbt --version

# Restore the image's default unprivileged user; transformation jobs are exec'd
# with `-u root` explicitly when they must write the DuckDB warehouse / ivy cache.
USER spark

WORKDIR /opt/spark/work-dir
