# syntax=docker/dockerfile:1
# ============================================================================
# Airflow 2.9.2 + platform DAG runtime
# ----------------------------------------------------------------------------
# Extends stock Airflow so the scheduler can actually RUN the platform DAGs:
#   * ingestion batch DAGs  -> in-process (PythonOperator): API -> Bronze/MinIO
#   * transformation DAG     -> dispatched into the spark-master container
#                               (docker exec via the mounted Docker socket)
#
# The repo is bind-mounted at runtime (PYTHONPATH=/opt/airflow/repo) so the
# `ingestion` / `transformation` packages import without a rebuild. Only the
# third-party runtime deps + the docker CLI are baked into the image, mirroring
# the spark-transform.Dockerfile pattern (build once, cache, no per-run pip).
# ============================================================================
FROM apache/airflow:2.9.2

# --- docker CLI (root) : lets BashOperator dispatch Spark/dbt into spark-master
# Only the client binary is installed (the daemon is the host's, reached via the
# mounted /var/run/docker.sock). curl + tar already ship in the Airflow image.
USER root
ARG DOCKER_CLI_VERSION=26.1.4
RUN curl -fsSL "https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_CLI_VERSION}.tgz" \
      | tar -xz -C /usr/local/bin --strip-components=1 docker/docker \
    && docker --version

# --- Python deps (airflow user) : ingestion connectors land Bronze in-process.
# Pinned to match ingestion/requirements.txt for reproducibility.
USER airflow
RUN pip install --no-cache-dir \
      "requests==2.32.3" \
      "boto3==1.34.131" \
      "kafka-python==2.0.2" \
      "sgp4==2.23" \
      "python-dotenv==1.0.1"
