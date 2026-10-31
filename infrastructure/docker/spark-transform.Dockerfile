# syntax=docker/dockerfile:1
# ============================================================================
# Spark 3.5.9 + dbt-duckdb transformation runner
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
FROM apache/spark:3.5.9-scala2.12-java17-python3-ubuntu

USER root

ADD --checksum=sha256:e9b54de76e530bb6cf0ccd036787103acb58fd42ba930ea8bf948ddbaa2f61d1 https://files.pythonhosted.org/packages/32/d1/a3652fe2c19134d0d15922177821d863cbd7e842d53a21bbe7e8e3a1b5ac/certifi-2026.10.23-py3-none-any.whl /tmp/certifi-2026.10.23-py3-none-any.whl

# This Spark image uses Python 3.10, allowing the current supported pip line.
# Seed pip's CA trust with a checksum-verified certifi wheel first.
RUN python3 -m pip install --no-index --no-deps /tmp/certifi-2026.10.23-py3-none-any.whl \
    && python3 -m pip config --global set global.cert "$(python3 -m certifi)" \
    && python3 -m pip install --no-cache-dir --upgrade "pip==26.2.2" \
    && python3 -m pip --version \
    && rm -f /tmp/certifi-2026.10.23-py3-none-any.whl

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
