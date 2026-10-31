# syntax=docker/dockerfile:1
# ============================================================================
# Airflow 2.9.2 + platform DAG runtime
# ----------------------------------------------------------------------------
# Extends stock Airflow so the scheduler can actually RUN the platform DAGs:
#   * ingestion batch DAGs   -> in-process (PythonOperator): API -> Bronze/MinIO
#   * transformation DAG     -> dispatched into the spark-master container
#                               (docker exec via the mounted Docker socket)
#   * pipelines/ DAGs (batch/streaming/master) -> orchestrate the above +
#                               serving + BI, logging run/row metrics to the
#                               shared Postgres `metadata` schema (psycopg2)
#                               and reading Silver/Gold/serving row counts via
#                               DuckDB httpfs (no Spark/dbt needed in-image).
#
# The repo is bind-mounted at runtime (PYTHONPATH=/opt/airflow/repo) so the
# `ingestion` / `transformation` / `pipelines` packages import without a
# rebuild. Only the third-party runtime deps + the docker CLI are baked into
# the image, mirroring the spark-transform.Dockerfile pattern (build once,
# cache, no per-run pip).
# ============================================================================
FROM apache/airflow:2.9.2

ADD --checksum=sha256:e9b54de76e530bb6cf0ccd036787103acb58fd42ba930ea8bf948ddbaa2f61d1 https://files.pythonhosted.org/packages/32/d1/a3652fe2c19134d0d15922177821d863cbd7e842d53a21bbe7e8e3a1b5ac/certifi-2026.10.23-py3-none-any.whl /tmp/certifi-2026.10.23-py3-none-any.whl

# --- docker CLI (root) : lets BashOperator dispatch Spark/dbt into spark-master
# Only the client binary is installed (the daemon is the host's, reached via the
# mounted /var/run/docker.sock). curl + tar already ship in the Airflow image.
USER root
ARG DOCKER_CLI_VERSION=26.1.4
RUN curl -fsSL "https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_CLI_VERSION}.tgz" \
      | tar -xz -C /usr/local/bin --strip-components=1 docker/docker \
    && docker --version

# Bootstrap the fixed CA bundle from a checksum-verified wheel before using pip
# over the network. The global pip setting also covers subsequent build/runtime
# installs, including Python 3.12's vendored pip certificate bundle.
RUN python3 -m pip install --no-index --no-deps /tmp/certifi-2026.10.23-py3-none-any.whl \
      && python3 -m pip config --global set global.cert "$(python3 -m certifi)" \
      && python3 -m pip install --no-cache-dir --upgrade "pip==26.2.2" \
      && python3 -m pip --version \
      && rm -f /tmp/certifi-2026.10.23-py3-none-any.whl

# --- Python deps (airflow user) : ingestion connectors land Bronze in-process.
# Pinned to match ingestion/requirements.txt for reproducibility.
USER airflow
RUN python3 -m pip install --no-cache-dir --upgrade \
      "pip==26.2.2" \
      "certifi==2026.10.23" \
    && python3 -m pip --version

RUN python3 -m pip install --no-cache-dir \
      "requests==2.32.3" \
      "boto3==1.34.131" \
      "kafka-python==2.0.2" \
      "sgp4==2.23" \
      "python-dotenv==1.0.1" \
      "earthengine-api==1.1.2" \
      "psycopg2-binary==2.9.9" \
      "duckdb>=0.9,<0.11"

# Pre-install DuckDB's httpfs extension at build time (pipelines.common.lake_metrics
# reads Silver/Gold Parquet straight from MinIO for row-count logging) so no task
# pays a runtime download; mirrors the dbt-duckdb pre-install in spark-transform.Dockerfile.
RUN python3 -c "import duckdb; con = duckdb.connect(); con.execute('install httpfs')"

