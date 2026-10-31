# syntax=docker/dockerfile:1
# ============================================================================
# Apache Superset + platform DB drivers
# ----------------------------------------------------------------------------
# The stock apache/superset:latest image is lean and ships NO database drivers,
# so it cannot reach either its own metadata store or the serving data layer.
# This image bakes in only what the BI stack needs (mirrors the
# airflow.Dockerfile / spark-transform.Dockerfile pattern: build once, no
# per-run pip):
#   * psycopg2-binary -> PostgreSQL metadata DB (superset schema/database)
#   * duckdb-engine   -> read-only serving DuckDB datasource (Gold via httpfs)
#
# Superset assets-as-code (bi/superset/**) and first-boot init (db upgrade +
# create-admin + init) are driven from docker-compose.bi.yml.
# ============================================================================
FROM apache/superset:latest

ADD --checksum=sha256:e9b54de76e530bb6cf0ccd036787103acb58fd42ba930ea8bf948ddbaa2f61d1 https://files.pythonhosted.org/packages/32/d1/a3652fe2c19134d0d15922177821d863cbd7e842d53a21bbe7e8e3a1b5ac/certifi-2026.10.23-py3-none-any.whl /tmp/certifi-2026.10.23-py3-none-any.whl

# The base image manages its runtime with `uv` inside the venv at /app/.venv,
# whose site-packages (NOT the system python) is what Superset imports from.
# Installing with plain `pip` lands in system site-packages and is invisible to
# Superset, so drivers must go through `uv` targeting the venv explicitly.
USER root
RUN /usr/local/bin/python -m pip install --no-index --no-deps /tmp/certifi-2026.10.23-py3-none-any.whl \
      && /usr/local/bin/python -m pip config --global set global.cert "$(/usr/local/bin/python -m certifi)" \
      && /usr/local/bin/python -m pip install --no-cache-dir --upgrade "pip==26.2.2" \
      && printf '%s\n' 'uv==0.13.6 --hash=sha256:22759b8895e1103578de6fb4cd27e94b4399d021023378d29f01333717751fba' > /tmp/uv-requirements.txt \
      && /usr/local/bin/python -m pip install --no-cache-dir --require-hashes --no-deps -r /tmp/uv-requirements.txt \
      && /usr/local/bin/python -m pip --version \
      && uv --version \
      && rm -f /tmp/uv-requirements.txt \
      && rm -f /tmp/certifi-2026.10.23-py3-none-any.whl \
      && VIRTUAL_ENV=/app/.venv uv pip install --no-cache \
      "certifi==2026.10.23" \
      "psycopg2-binary==2.9.9" \
      "duckdb-engine==0.13.2"

USER superset
