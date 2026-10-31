# Operations Runbook

> **Living operational cheat-sheet** for the Space Mission Data & AI Platform.
> Day-to-day commands to run, start/stop, inspect, and query the platform.
> Updated each phase — see the [Phase Status & Changelog](#phase-status--changelog) at the bottom.

This runbook is **PowerShell-first** (Windows + Docker Desktop), with the equivalent
`bash` convenience scripts noted where they exist. The deeper *design* rationale
lives in [docs/infrastructure/](docs/infrastructure/README.md); this file is the
hands-on operator guide.

---

## Table of Contents

1. [Conventions & one-time setup](#1-conventions--one-time-setup)
2. [Start / stop the platform](#2-start--stop-the-platform)
3. [Status & health checks](#3-status--health-checks)
4. [Logs, resources, troubleshooting](#4-logs-resources-troubleshooting)
5. [Service URLs & login guidance](#5-service-urls--login-guidance)
6. [Querying PostgreSQL yourself](#6-querying-postgresql-yourself)
7. [Object storage (MinIO) — buckets & files](#7-object-storage-minio--buckets--files)
8. [Viewing & querying Bronze / Silver / Gold](#8-viewing--querying-bronze--silver--gold)
9. [Kafka operations](#9-kafka-operations)
10. [Running the ingestion layer](#10-running-the-ingestion-layer)
11. [Running the transformation layer](#11-running-the-transformation-layer)
12. [Full end-to-end platform run (infra → ingestion → transformation → serving → BI)](#12-full-end-to-end-platform-run-infra--ingestion--transformation--serving--bi)
13. [Manual data verification & validation (per stage)](#13-manual-data-verification--validation-per-stage)
14. [Airflow-orchestrated pipelines & run-logging (pipelines/)](#14-airflow-orchestrated-pipelines--run-logging-pipelines)
15. [Phase status & changelog](#phase-status--changelog)

---

## 1. Conventions & one-time setup

### Where commands run

All Docker commands run from the **docker compose directory**. Because the platform
uses six modular stack files, set a reusable Compose context **once per terminal**:

```powershell
# Run once per PowerShell session
Set-Location "c:\D Drive\Projects\DE\Projects\space-data-ai-platform\infrastructure\docker"

$ALL = @(
  '-f','docker-compose.yml',
  '-f','docker-compose.storage.yml',
  '-f','docker-compose.ingestion.yml',
  '-f','docker-compose.processing.yml',
  '-f','docker-compose.ai.yml',
  '-f','docker-compose.observability.yml',
  '-f','docker-compose.bi.yml',
  '--env-file','../env/.env'
)

# Then every command becomes:  docker compose @ALL <command>
docker compose @ALL ps
```

> Containers are **project-prefixed** (`space-platform-<service>-1`). Always address
> services by their **service name** (`postgres`, `minio`, …) through
> `docker compose @ALL exec <service>` — never `docker exec postgres`.

### One-time initialization

```powershell
# 1. Create your local env file from the template (git-ignored)
Copy-Item ../env/.env.example ../env/.env
# 2. Edit ../env/.env — replace every CHANGE_ME_* value, fill any API keys

# 3. Bootstrap: create PostgreSQL schemas + MinIO buckets (idempotent)
#    Easiest cross-platform path is the bash script (WSL / Git Bash):
bash ../scripts/bootstrap.sh
```

**PowerShell-only equivalent** (no bash), after storage is up (see §2):

```powershell
# Schemas
$env:PGPASSWORD = (Select-String '../env/.env' -Pattern '^POSTGRES_PASSWORD=').Line.Split('=')[1]
foreach ($s in 'metadata','gold','iceberg_catalog','airflow','mlflow','superset','feast') {
  docker compose @ALL exec -T postgres psql -U platform -d platform -c "CREATE SCHEMA IF NOT EXISTS $s;"
}
# Buckets (one-off mc client on the data network)
$minioPass = (Select-String '../env/.env' -Pattern '^MINIO_ROOT_PASSWORD=').Line.Split('=')[1]
$minioUser = (Select-String '../env/.env' -Pattern '^MINIO_ROOT_USER=').Line.Split('=')[1]
docker run --rm --network space-data-net -e MC_HOST_local="http://${minioUser}:${minioPass}@minio:9000" `
  minio/mc mb --ignore-existing local/bronze local/silver local/gold local/warehouse local/mlflow-artifacts local/staging
```

---

## 2. Start / stop the platform

Services are grouped into **profiles**. Start the smallest set you need — on a 16 GB
laptop, avoid running the Spark (`processing`) and Ollama (`ai`) peaks at the same time.

| Profile | Stacks started | Approx. idle RAM |
| --- | --- | --- |
| `storage` | postgres, minio, iceberg-rest | ~2 GB |
| `core` | storage + kafka + spark + airflow | ~7 GB |
| `ai` | storage + mlflow, jupyter, qdrant, ollama, open-webui | ~7 GB |
| `obs` | storage + prometheus, grafana, otel | ~3 GB |
| `bi` | storage + superset | ~3 GB |
| `all` | everything (mind the Spark+Ollama peak) | ~10 GB |

### Start

```powershell
# Foundation only
docker compose @ALL --profile storage up -d

# Data-engineering core (storage + ingestion + processing)
docker compose @ALL --profile core up -d

# Observability stack
docker compose @ALL --profile obs up -d

# BI (Superset) — needs storage too (Superset depends on postgres)
docker compose @ALL --profile storage --profile bi up -d

# Everything
docker compose @ALL --profile all up -d

# A single service (dependencies start automatically)
docker compose @ALL --profile core up -d kafka
```

> `depends_on` health conditions make Compose wait for upstreams (e.g. `postgres`
> healthy) before starting dependents, so a single `up -d` brings a profile up in order.

**Bash convenience scripts** (staged startup with explicit health waits, WSL / Git Bash):

```bash
bash ../scripts/start-platform.sh --profile core   # storage|core|ai|obs|all
```

### Stop

```powershell
# Stop everything, KEEP all data (named volumes preserved)
docker compose @ALL --profile all down

# Stop a single stack's services (example: processing)
docker compose @ALL --profile core stop spark-master spark-worker airflow
```

```bash
bash ../scripts/stop-platform.sh        # graceful stop, data preserved
```

### Reset (DESTRUCTIVE)

```powershell
# Removes containers, networks AND volumes — wipes all data. Backup first!
docker compose @ALL --profile all down -v
```

```bash
bash ../scripts/reset-platform.sh       # backs up Postgres + key buckets, then wipes
```

---

## 3. Status & health checks

```powershell
# Compose view of targeted services (status + health + ports)
docker compose @ALL ps

# All running platform containers with health
docker ps --filter "name=space-platform" --format "table {{.Names}}\t{{.Status}}"

# Health of one service
docker inspect space-platform-airflow-1 --format '{{.State.Health.Status}}'
```

### Quick verification checklist

```powershell
# PostgreSQL reachable + list schemas
docker compose @ALL exec -T postgres psql -U platform -d platform -c "\dn"

# MinIO buckets present (via console UI is easiest — see §5/§7)

# Kafka broker reachable + list topics
docker compose @ALL exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list

# Iceberg REST catalog config (from inside the data network)
docker run --rm --network space-data-net curlimages/curl:latest -s http://iceberg-rest:8181/v1/config
```

Expected after bootstrap: schemas `metadata, gold, iceberg_catalog, airflow, mlflow,
superset, feast`; buckets `bronze, silver, gold, warehouse, mlflow-artifacts, staging`.

---

## 4. Logs, resources, troubleshooting

```powershell
# Tail logs for a service
docker compose @ALL logs -f airflow

# Last 80 lines, no follow
docker compose @ALL logs --tail 80 spark-master

# Live resource usage (RAM/CPU per container)
docker stats --no-stream

# Restart a single service
docker compose @ALL restart grafana

# Recreate a service after editing its compose/healthcheck
docker compose @ALL up -d --force-recreate iceberg-rest
```

| Symptom | Likely cause / fix |
| --- | --- |
| `Conflict. The container name "minio" is already in use` | A *different* project squats the name. This platform uses project-prefixed names; ensure you pull latest compose. Remove the stray container or stop the other project. |
| Service stuck `health: starting` then `unhealthy` on first boot | Slow first-boot (Airflow/Superset). `start_period` grace windows are configured; it recovers on the next successful probe. |
| `psql: could not connect` from host tools | PostgreSQL port is **not published**; query via `docker compose @ALL exec postgres psql …` (see §6). |
| Out of memory / Docker freezes | Run one heavy profile at a time; never peak `processing` (Spark) and `ai` (Ollama) together. |

---

## 5. Service URLs & login guidance

> Replace passwords with the values in your `../env/.env`. Print one quickly:
> `(Select-String '../env/.env' -Pattern '^GRAFANA_ADMIN_PASSWORD=').Line`

| Service | URL | Login |
| --- | --- | --- |
| MinIO Console | http://localhost:9001 | user `MINIO_ROOT_USER` (default `platform_minio`) / `MINIO_ROOT_PASSWORD` |
| Kafka UI | http://localhost:8088 | no auth |
| Spark Master UI | http://localhost:8080 | no auth |
| Spark Worker UI | http://localhost:8081 | no auth |
| Airflow | http://localhost:8082 | user `admin` (`AIRFLOW_ADMIN_USER`) / `AIRFLOW_ADMIN_PASSWORD` |
| MLflow | http://localhost:5000 | no auth |
| Jupyter Lab | http://localhost:8888 | token = `JUPYTER_TOKEN` (append `?token=…`) |
| Qdrant dashboard | http://localhost:6333/dashboard | no auth |
| Open WebUI (LLM) | http://localhost:3000 | auth disabled (`WEBUI_AUTH=false`) |
| Prometheus | http://localhost:9090 | no auth |
| Grafana | http://localhost:3001 | user `admin` (`GRAFANA_ADMIN_USER`) / `GRAFANA_ADMIN_PASSWORD` |
| Superset | http://localhost:8089 | user `admin` (`SUPERSET_ADMIN_USER`) / `SUPERSET_ADMIN_PASSWORD` |
| FastAPI (later phase) | http://localhost:8000 | — |

**Airflow admin password.** Login credentials are declarative, read from
`infrastructure/env/.env` (`AIRFLOW_ADMIN_USER` / `AIRFLOW_ADMIN_PASSWORD`, same
pattern as `SUPERSET_ADMIN_USER`/`SUPERSET_ADMIN_PASSWORD` and
`GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD`) — **not** Airflow's own
auto-generated-on-first-boot password. That auto-generated file
(`/opt/airflow/standalone_admin_password.txt`) lives outside any persisted volume, so
it silently disappears the next time the container is recreated even though the
`admin` account itself persists (it lives in the `airflow` PostgreSQL schema, which
*is* persistent) — relying on it turned out to be a dead end after the first boot, so
the `airflow` service's `command` now creates the user (or resets its password if it
already exists) from those two env vars **every time the container starts**,
converging the login to whatever is currently in `.env`:

```powershell
# Change the password: edit AIRFLOW_ADMIN_PASSWORD in infrastructure/env/.env, then
docker compose @ALL up -d --force-recreate airflow

# Verify the account exists / is active:
docker compose @ALL exec airflow airflow users list
```

### Trigger ingestion & transformation jobs from the UI

The **processing** stack builds a custom Airflow image (`airflow.Dockerfile`) that mounts
the repo, installs the ingestion + pipelines runtime deps (incl. `psycopg2`, `duckdb`,
`earthengine-api`), and mounts the Docker socket. The DAGs appear at `http://localhost:8082`:

| DAG | What it does | Runs | Schedule |
| --- | --- | --- | --- |
| `ingest_nasa_power` / `ingest_nasa_firms` / `ingest_noaa_swpc` / `ingest_celestrak_tle` / `ingest_openaq` / `ingest_tropomi` / `ingest_modis_aod` | One API connector → Bronze/MinIO | **in-process** in the Airflow container | Scheduled (per-source cadence) |
| `transformation_medallion_batch` | 10× Bronze→Silver (sim + MVP EO + climate, Spark, run **sequentially**) → Gold lakehouse (Spark → `s3://gold`) → Gold dbt demonstrator | **dispatched into `spark-master`** via `docker exec` | Daily `0 1 * * *` |
| `platform_batch_pipeline` | Full batch track: ingestion (every source) → transformation (10 Silver + 14 Gold marts + dbt demonstrator) → serving (dbt build) → bi (Superset dataset refresh). Logs run/row metrics to `metadata.*` — see [§14](#14-airflow-orchestrated-pipelines--run-logging-pipelines) | Mixed: ingestion + bi in-process, transformation + serving via `docker exec` | **Manual only** |
| `platform_streaming_pipeline` | Bounded streaming demo: telemetry produce → Bronze raw-consume → validate, then a Spark Structured Streaming windowed transform (start → 2 real waves to advance the watermark → stop) | Mixed (in-process + `docker exec`) | **Manual only** |
| `platform_master_pipeline` | Triggers `platform_batch_pipeline` fully, then `platform_streaming_pipeline` | Orchestrates the two DAGs above (`TriggerDagRunOperator`, waits for completion) | **Manual only** |

Steps:

1. Open `http://localhost:8082`, log in as `admin` (password above).
2. Toggle a DAG **On** (unpause) to let it run on schedule, or click **▶ Trigger DAG** for
   an immediate run. The three `platform_*` DAGs have no schedule — they only ever run
   when triggered (UI button or `airflow dags trigger <dag_id>`).
3. Watch progress in **Grid/Graph**; task logs are in the UI (and the `airflow-logs` volume).

> **Prerequisites.** Transformation needs Bronze seeded and `spark-master` healthy (see
> §11). The transformation DAGs shell into the container named `space-platform-spark-master-1`
> (compose default); if your project name differs, set `SPARK_CONTAINER` on the `airflow`
> service. On Linux-native Docker (not Docker Desktop) the `airflow` user may need the host
> Docker group — add `group_add: ["<docker-gid>"]` to the service.
>
> **`platform_batch_pipeline` takes ~35-45 minutes** (real API calls + sequential Spark
> jobs) and **`platform_streaming_pipeline` takes ~3-5 minutes** (deliberately bounded
> waits for the watermark to advance) — trigger them and check back rather than waiting
> synchronously. See [§14](#14-airflow-orchestrated-pipelines--run-logging-pipelines) for
> how to monitor and query results without babysitting the UI.

---

## 6. Querying PostgreSQL yourself

PostgreSQL hosts the `gold` serving tables plus metadata for Airflow/MLflow/Superset/
Feast. The port is intentionally **not** exposed to the host; query through the container.

```powershell
# Interactive psql session (database: platform, user: platform)
docker compose @ALL exec postgres psql -U platform -d platform
```

Useful psql meta-commands once inside:

```text
\dn               -- list schemas
\dt gold.*        -- list tables in the gold schema
\d gold.<table>   -- describe a table
\du               -- list roles (note: analyst_ro is a read-only role on gold)
\q                -- quit
```

One-off queries (non-interactive):

```powershell
# List all schemas
docker compose @ALL exec -T postgres psql -U platform -d platform -c "\dn"

# List tables in gold
docker compose @ALL exec -T postgres psql -U platform -d platform -c "\dt gold.*"

# Run an ad-hoc query
docker compose @ALL exec -T postgres psql -U platform -d platform -c "SELECT * FROM gold.<table> LIMIT 20;"

# Pipe a .sql file from the host
Get-Content .\my_query.sql | docker compose @ALL exec -T postgres psql -U platform -d platform
```

**Using a GUI client (DBeaver / pgAdmin):** the host port is closed by default. To connect
a desktop client, publish the port by adding `ports: ["5432:5432"]` to the `postgres`
service in `docker-compose.storage.yml`, then connect to `localhost:5432`, db `platform`,
user `platform`. (Left closed by default to avoid clashing with other local Postgres.)

> Note: until the serving phase populates `gold`, these queries return empty result sets —
> the schemas exist but contain no business tables yet.

---

## 7. Object storage (MinIO) — buckets & files

The lakehouse layers live as objects in MinIO (S3-compatible). Two ways to browse:

**A) MinIO Console (easiest):** open http://localhost:9001 and log in with the MinIO
credentials. Browse buckets `bronze / silver / gold / warehouse / mlflow-artifacts / staging`.

**B) `mc` CLI (scriptable, one-off container on the data network):**

```powershell
# Build a reusable mc host string from your .env
$u = (Select-String '../env/.env' -Pattern '^MINIO_ROOT_USER=').Line.Split('=')[1]
$p = (Select-String '../env/.env' -Pattern '^MINIO_ROOT_PASSWORD=').Line.Split('=')[1]
$MC = @('run','--rm','--network','space-data-net','-e',"MC_HOST_local=http://${u}:${p}@minio:9000",'minio/mc')

# List all buckets
docker @MC ls local/

# List objects in a bucket (recursive)
docker @MC ls --recursive local/bronze

# Show object size/metadata
docker @MC stat local/gold/<path/to/object>

# Print a (text/JSON) object to stdout
docker @MC cat local/staging/<path/to/file.json>

# Copy an object out to the host
docker @MC cp local/gold/<object> /tmp/out && docker @MC --help | Out-Null
```

> Buckets are created empty by bootstrap. They fill up once the ingestion and
> transformation phases write data (see changelog).

---

## 8. Viewing & querying Bronze / Silver / Gold

The medallion layers are served three ways depending on what you want:

| Layer | Where it lives | Query method |
| --- | --- | --- |
| **Bronze** (raw) | MinIO `bronze/` (+ Iceberg in `warehouse/`) | MinIO console / `mc`; Spark SQL on the `lakehouse` catalog |
| **Silver** (conformed) | Iceberg tables in `warehouse/` (MinIO) | Spark SQL on the `lakehouse` catalog; DuckDB |
| **Gold** (serving) | Iceberg `warehouse/` **and** PostgreSQL `gold` schema | `psql` (§6) for relational gold; Spark SQL for Iceberg gold |

### Spark SQL over the Iceberg lakehouse

The Spark config wires an Iceberg **REST catalog named `lakehouse`**
(warehouse `s3://warehouse/`, via `iceberg-rest` + MinIO). With the `processing`
stack running:

```powershell
# Open a Spark SQL shell (requires the Iceberg + S3 runtime jars — see note)
docker compose @ALL exec `
  -e AWS_ACCESS_KEY_ID=$u -e AWS_SECRET_ACCESS_KEY=$p `
  spark-master /opt/spark/bin/spark-sql `
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2,org.apache.hadoop:hadoop-aws:3.3.4
```

```sql
-- Inside spark-sql:
SHOW NAMESPACES IN lakehouse;            -- bronze, silver, gold (once created)
SHOW TABLES IN lakehouse.silver;
SELECT * FROM lakehouse.gold.<table> LIMIT 20;
```

> The base `apache/spark:3.5.9-scala2.12-java17-python3-ubuntu` image does not bundle the Iceberg/S3 jars, so the
> first run downloads them via `--packages` (needs internet). The **transformation
> phase** ships preconfigured Spark jobs and `make` targets so you won't pass
> `--packages` by hand for the medallion pipeline — see [§11](#11-running-the-transformation-layer).

### DuckDB (lightweight, 16 GB-friendly)

DuckDB can read Parquet/Iceberg directly from MinIO and is ideal for quick local
analysis. It is introduced as part of the transformation phase; a ready example
(`duckdb` + `httpfs`/`iceberg` extensions pointed at `http://localhost:9000`) will be
added here once that phase lands.

> **Current state (Phase 9):** the full medallion flow is runnable end-to-end. **Bronze**
> holds real landed data (raw telemetry + API objects under `bronze/<SOURCE>/ingest_date=…/`,
> §10). **Silver** Parquet (`silver/silver_telemetry|orbit|space_weather`, plus the
> streaming `silver/stream_sat_health_1m`) and the **Gold** dbt marts are produced by the
> one-command transformation pipeline in §11. The Iceberg/Spark-SQL commands above remain
> the mechanism for ad-hoc lakehouse querying.

---

## 9. Kafka operations

With the `ingestion` (or `core`) stack running:

```powershell
# List topics
docker compose @ALL exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list

# Describe a topic
docker compose @ALL exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic <topic>

# Create a topic (manual; pipelines create their own later)
docker compose @ALL exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic demo --partitions 3 --replication-factor 1

# Consume the latest messages from a topic
docker compose @ALL exec -T kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic <topic> --from-beginning --max-messages 10
```

Or use **Kafka UI** at http://localhost:8088 to browse topics, partitions, and messages.

---

## 10. Running the ingestion layer

The ingestion code lives in [ingestion/](ingestion/README.md) (streaming producers/consumers,
API connectors, synthetic generators, quality + Bronze landing). This section is the
**operator** guide for running it against the live platform.

### Why ingestion runs *inside* the Docker network

Kafka advertises only `INTERNAL://kafka:9092` and is **not published to the host**, so a
producer/consumer started from your laptop shell **cannot reach the broker**. Run the
ingestion modules from a throwaway container attached to the platform network. Kafka and
MinIO both share **`space-ops-net`**, so a single attachment reaches both by DNS
(`kafka:9092`, `minio:9000`).

> Offline development (no infra) still works from the host: `make test` and `make demo`
> exercise the full logical flow in-memory — see [ingestion/README.md](ingestion/README.md).

### One-time: start a reusable ingestion runner

With the `storage` + `ingestion` (and `processing` for Airflow) stacks up (see §2):

```powershell
$REPO = "c:\D Drive\Projects\DE\Projects\space-data-ai-platform"
docker rm -f space-ingest-runner 2>$null
docker run -d --name space-ingest-runner --network space-ops-net `
  -v "${REPO}:/work" -w /work `
  -e KAFKA_BOOTSTRAP=kafka:9092 -e MINIO_ENDPOINT=http://minio:9000 `
  python:3.11-slim sleep infinity
docker exec space-ingest-runner pip install -q -r ingestion/requirements.txt
```

> The runner bind-mounts the repo, so code edits are picked up immediately. Credentials
> (MinIO + API keys) are read from the mounted `infrastructure/env/.env`; the `-e`
> endpoint overrides win because `load_dotenv` runs with `override=False`.

### A) Synthetic streaming pipeline (telemetry → Bronze → cleaned/DLQ)

```powershell
# 1. Create the Kafka topics (idempotent)
docker exec space-ingest-runner python -m ingestion.scripts.create_topics

# 2. Produce N synthetic telemetry records to telemetry.satellite.raw
docker exec space-ingest-runner python -m ingestion.streaming.producers.telemetry_producer --max 300 --rate 200

# 3. Land raw telemetry in Bronze (MinIO). Size the run so it exits cleanly:
#    consumers have no idle timeout, so --max-batches * --batch-size must cover the produced count.
docker exec space-ingest-runner python -m ingestion.streaming.consumers.raw_ingest_consumer --batch-size 100 --max-batches 3

# 4. Validate raw -> cleaned topic / quarantine + DLQ (reads the same topic, different group)
docker exec space-ingest-runner python -m ingestion.streaming.consumers.validation_consumer --max 300
```

### B) API connectors → Bronze (real online sources)

Anonymous sources need no keys; keyed sources read credentials from `infrastructure/env/.env`.

| Connector | Source | Auth |
| --- | --- | --- |
| `PowerConnector` | NASA POWER (daily weather) | anonymous |
| `SwpcConnector` | NOAA SWPC (planetary K-index) | anonymous |
| `CelestrakConnector` | CelesTrak GP/TLE | anonymous |
| `FirmsConnector` | NASA FIRMS / VIIRS active fire | `FIRMS_MAP_KEY` |
| `GfwConnector` | Global Fishing Watch (vessel identity) | `GFW_API_TOKEN` |
| `SentinelHubConnector` | Sentinel Hub Catalog (STAC scene metadata) | `SENTINELHUB_CLIENT_ID` / `_SECRET` |

```powershell
# Land a batch from any connector to Bronze (example: NASA POWER + NOAA SWPC + CelesTrak)
docker exec space-ingest-runner python -c "
from ingestion.batch.ingest_task import run_connector_to_bronze
from ingestion.api.nasa_power import PowerConnector
from ingestion.api.noaa_swpc import SwpcConnector
from ingestion.api.celestrak import CelestrakConnector
for c in (PowerConnector(), SwpcConnector(), CelestrakConnector()):
    print(run_connector_to_bronze(c))
"

# Keyed sources (keys must be set in infrastructure/env/.env)
docker exec space-ingest-runner python -c "
from ingestion.batch.ingest_task import run_connector_to_bronze
from ingestion.api.nasa_firms import FirmsConnector
from ingestion.api.gfw import GfwConnector
print(run_connector_to_bronze(FirmsConnector(), source='VIIRS_SNPP_NRT', area='-10,-10,10,10', days=1))
print(run_connector_to_bronze(GfwConnector(), query='Maria', limit=20))
"
```

The two frequently-updating sources can instead be **bridged to Kafka** (request/response → stream):

```powershell
docker exec space-ingest-runner python -m ingestion.streaming.producers.api_bridge_producer --source swpc       # -> space.weather.events
docker exec space-ingest-runner python -m ingestion.streaming.producers.api_bridge_producer --source celestrak  # -> orbit.position.stream
```

### Verify the run

```powershell
# Kafka end offsets (message counts) per topic
docker exec space-ingest-runner python -c "
from kafka import KafkaConsumer
from kafka.structs import TopicPartition as TP
c=KafkaConsumer(bootstrap_servers='kafka:9092')
for t in ['telemetry.satellite.raw','telemetry.satellite.cleaned','telemetry.satellite.dlq','space.weather.events','orbit.position.stream']:
    ps=c.partitions_for_topic(t) or set(); tps=[TP(t,p) for p in ps]
    print(t, sum(c.end_offsets(tps).values()) if tps else 0)
c.close()"

# Bronze object counts per source (in MinIO)
docker exec space-ingest-runner python -c "
import boto3; from botocore.config import Config
from ingestion.config.settings import settings as s
cl=boto3.client('s3',endpoint_url=s.minio.endpoint,aws_access_key_id=s.minio.access_key,aws_secret_access_key=s.minio.secret_key,region_name=s.minio.region,config=Config(s3={'addressing_style':'path'}))
for p in ['telemetry/','POWER/','SWPC/','CELESTRAK/','FIRMS/','GFW/','SENTINELHUB/']:
    objs=cl.list_objects_v2(Bucket='bronze',Prefix=p).get('Contents',[])
    print(p, len(objs), 'objs', sum(o['Size'] for o in objs), 'bytes')"
```

You can also browse the landed objects in the **MinIO Console** (§7) under `bronze/<SOURCE>/ingest_date=YYYY-MM-DD/<batch_id>/part-0000.jsonl`, or inspect topics in **Kafka UI** (§9).

### Clean up the runner

```powershell
docker rm -f space-ingest-runner
```

| Symptom | Likely cause / fix |
| --- | --- |
| Producer raises `Unrecognized configs: {'enable_idempotence': True}` | Old code with a config unsupported by `kafka-python==2.0.2`; pull latest (`create_producer` no longer sets it). |
| A consumer **hangs** after draining the topic | Consumers have no idle timeout. Bound them: `raw_ingest_consumer --batch-size B --max-batches N` (cover the produced count) and `validation_consumer --max N`. |
| `NoBrokersAvailable` from the host shell | You ran a module from the laptop, not the runner. Kafka isn't published to the host — run inside `space-ingest-runner` (above). |
| Keyed connector raises `... is not configured` | The API key/secret is missing from `infrastructure/env/.env`. |
| API connector read-timeout | Transient upstream/network issue; the resilient client already retries 4× with backoff. Re-run the connector. |

---

## 11. Running the transformation layer

The transformation code lives in [transformation/](transformation/README.md) (Spark
Bronze→Silver jobs, dbt Gold marts, and a Kafka→Silver streaming job). Unlike Phase 8,
this layer runs **inside the `spark-master` container itself** — that service is now a
**hardened image** (`space-platform/spark-transform:3.5.9` = `apache/spark:3.5.9-scala2.12-java17-python3-ubuntu` +
`dbt-duckdb`) with the repo bind-mounted and MinIO/Kafka wiring baked into its
environment. A cold `up` therefore needs **no** `docker cp`, runtime `pip install`, or
manual `docker network connect`.

> Offline development (no infra) still works from the host: `make -C transformation test`
> and `make -C transformation demo` run the full logical flow in-memory — see
> [transformation/README.md](transformation/README.md).

### Why it runs *inside* `spark-master`

The driver executes in `local[*]` mode inside `spark-master`, which is attached to
`compute-net` + `data-net` (S3A → MinIO) **and** `stream-net` (Kafka). Jobs are exec'd
with `-u root` because they write the DuckDB warehouse and the Ivy jar cache. All the
required env (`MINIO_ENDPOINT`, `MINIO_ROOT_USER/PASSWORD`, `KAFKA_BOOTSTRAP`,
`DUCKDB_S3_ENDPOINT`, `DBT_PROFILES_DIR`, `DBT_DUCKDB_PATH`) is set by the compose file.

> **First `up` builds the image** (installs dbt, ~6 min) then caches it; the Ivy jar
> cache (`spark-ivy` volume) means the S3A/Kafka connectors download only once.

### Step 0 — seed Bronze (only after a fresh start or `down -v`)

Silver reads enveloped Bronze NDJSON from `s3://bronze/{satellite_telemetry,orbit_position,space_weather}/`.
Bronze survives stop/start and `down`/`up`, so seed only when the MinIO volume is empty
(first boot or after a reset). Generate the records inside `spark-master` (it has the
ingestion code), then upload with a one-off `mc` client:

```powershell
$REPO = "c:\D Drive\Projects\DE\Projects\space-data-ai-platform"

# 1. Generate enveloped Bronze NDJSON into the bind-mounted transformation dir
docker compose @ALL exec -u root spark-master `
  python3 -m transformation.scripts.seed_bronze_lake `
  --records 120 --out /opt/spark/work-dir/transformation/.bronze_seed

# 2. Upload each dataset to s3://bronze/<dataset>/ (reuse $u/$p from §7)
foreach ($d in 'satellite_telemetry','orbit_position','space_weather') {
  docker run --rm --network space-data-net -v "${REPO}:/work" `
    -e MC_HOST_local="http://${u}:${p}@minio:9000" minio/mc `
    cp "/work/transformation/.bronze_seed/$d.json" "local/bronze/$d/$d.json"
}
```

### A) Batch pipeline — Bronze → Silver → Gold (one command)

```powershell
# Runs every Silver job (sim + MVP EO, one at a time), then the Spark Gold
# lakehouse writer (all marts -> s3://gold), then dbt deps/run/test (demonstrator)
docker compose @ALL exec -u root spark-master `
  bash /opt/spark/work-dir/transformation/scripts/run_pipeline.sh
```

Equivalent `make` targets (from the repo root; needs `make` on PATH):

```powershell
make -C transformation pipeline-infra              # full Bronze→Silver→Gold
make -C transformation silver-infra ENTITY=orbit   # a single Silver entity
make -C transformation gold-infra                  # just the dbt Gold marts
```

**Silver entities** (`run_silver.py <entity>`): simulation track `telemetry`,
`orbit`, `space_weather`; MVP Earth-observation `fire` (FIRMS), `vessel` (GFW),
`scene` (Sentinel Hub / Landsat / Earthdata), `index` (Sentinel Hub NDVI/NDWI/NBR).
An absent Bronze source is skipped inside `run_spark`, so a partial ingest still
produces Silver. EO Silver rows carry all-null columns; explicit Spark schemas
(`_silver_spark_schema`) + `coerce_rows_to_schema` make the Parquet write
deterministic.

**Gold lakehouse** (`run_gold.py`): materialises all ten business-ready marts to
`s3://gold/<table>/*.parquet` — the **only** serving source. It reuses the tested
pure-Python `silver_to_gold` rules (point-in-polygon AOI attribution can't be
expressed in dbt SQL, ADR-SV-01) and loads the Copernicus-EMS AOI reference seed
(`transformation/seeds/aoi_reference.geojson`) as `ref_aoi` + validation ground
truth. Marts: `kpi_wildfire_aoi_daily`, `kpi_flood_aoi_daily`,
`fact_vessel_activity`, `fact_scene_catalog`, `kpi_eo_daily`, `kpi_aoi_validation`,
`ref_aoi` (MVP EO) + `fact_sat_health`, `kpi_launch_monthly`, `fact_weather_impact`
(sim). Marts with no source data land an empty (0-row) Parquet so the serving
contract stays stable.

Expected: each `silver_*` lands `_SUCCESS` + Parquet in `s3://silver/`; the Gold
writer logs `wrote gold/<table>: N row(s)` for all ten marts to `s3://gold/`; the
dbt demonstrator reports `run PASS` + `test PASS`. The Gold DuckDB warehouse (sim
demonstrator) persists at `transformation/dbt/space.duckdb`.

### B) Streaming job — Kafka → Silver windows

Reads `telemetry.satellite.cleaned` (produced in §10), computes 1-minute sliding health
windows, and writes Parquet to `s3://silver/stream_sat_health_1m/`. It runs continuously
(`awaitTermination`), so launch it detached and stop it when done:

```powershell
# Launch the streaming query (long-running — runs until stopped)
make -C transformation stream-infra
# …or directly:
docker compose @ALL exec -u root spark-master /opt/spark/bin/spark-submit `
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.9,org.apache.hadoop:hadoop-aws:3.3.4 `
  --conf spark.jars.ivy=/tmp/.ivy2 --conf spark.sql.extensions= `
  --conf spark.driver.host=localhost --conf spark.driver.bindAddress=127.0.0.1 `
  /opt/spark/work-dir/transformation/scripts/run_stream.py
```

> Append-mode windows only flush once the watermark passes a window's end, so the first
> Parquet file is empty and real rows appear after 2–3 triggers. Produce a second wave of
> (later-timestamped) telemetry to advance the watermark, then re-list `s3://silver/stream_sat_health_1m/`.

### C) Serving data products — Gold → dbt products

Builds the business-facing serving products (wildfire/flood/vessel/scene/AOI-validation +
the platform-KPI materialised view) by reading the Gold Parquet directly from MinIO with
DuckDB + `httpfs` — no serving database server. Runs as a one-off container from the
`spark-transform` image (which carries dbt-duckdb), on `space-data-net`:

```powershell
$p = (Get-Content infrastructure/env/.env | Select-String '^MINIO_ROOT_PASSWORD=' |
      ForEach-Object { ($_ -split '=',2)[1] })
docker run --rm --network space-data-net --user root --entrypoint bash `
  -v "${PWD}:/work" `
  -e DBT_PROFILES_DIR=/work/serving/dbt -e SERVING_DUCKDB_PATH=/work/serving/dbt/serving.duckdb `
  -e DUCKDB_S3_ENDPOINT=minio:9000 `
  -e MINIO_ROOT_USER=platform_minio -e MINIO_ROOT_PASSWORD=$p `
  space-platform/spark-transform:3.5.9 `
  -lc "cd /work/serving/dbt && dbt deps && dbt run && dbt test"
```

Expect: `dbt run` builds every `serving_*` model + `mv_kpi_platform_daily`/`mv_kpi_climate_daily`; `dbt test`
reports `PASS=52`. Serving reads **only** `s3://gold/<table>/*.parquet`, so run the batch
pipeline (A) first. **Always set `SERVING_DUCKDB_PATH` to the bind-mounted
`/work/serving/dbt/serving.duckdb`** — that exact file is what `bi.yml` mounts read-only
into Superset (`/opt/serving/serving_products.duckdb`); building into a container-local
`/tmp` path (as some older one-liners do) silently leaves Superset on stale data.

### Verify the run

```powershell
# Silver/Gold object listing
docker @MC ls --recursive local/silver

# Gold lakehouse marts (serving source)
docker @MC ls local/gold

# Query the Gold DuckDB warehouse (root-owned; query as root)
docker compose @ALL exec -u root spark-master `
  python3 -c "import duckdb; c=duckdb.connect('/opt/spark/work-dir/transformation/dbt/space.duckdb'); print(c.execute('select * from gold.fact_sat_health').fetchall())"
```

| Symptom | Likely cause / fix |
| --- | --- |
| Silver job fails with `Path does not exist: s3a://bronze/…` | Bronze not seeded. Run Step 0 (only needed after a fresh start / `down -v`). |
| Streaming raises `No resolvable bootstrap urls` / DNS for `kafka` | `spark-master` not on `stream-net`. The hardened compose attaches it automatically — pull latest and `up -d --force-recreate spark-master`. |
| dbt / DuckDB `Permission denied` writing `space.duckdb` | Run the job with `-u root` (the warehouse + Ivy cache are root-owned). |
| `BlockManager` NullPointerException during Silver | Two Spark drivers ran concurrently. `run_pipeline.sh` runs entities one at a time — don't launch parallel jobs. |
| First batch job is slow (~minutes) | First-ever run downloads `hadoop-aws`/Kafka jars into the `spark-ivy` cache; later runs are fast. |

---

## 12. Full end-to-end platform run (infra → ingestion → transformation → serving → BI)

This section chains every layer above into one repeatable "cold start to dashboards"
run. Follow it top to bottom; each step links back to its detailed section.

### Step 0 — Pre-flight: verify every data-source credential

Before ingesting anything, confirm every API key/account in `infrastructure/env/.env`
is actually valid (not just present). The [pre-flight tool](tools/datasource-preflight/README.md)
normally reads its own local `.env`; [`preflight_infra_env.py`](tools/datasource-preflight/preflight_infra_env.py)
is a thin wrapper that loads the **shared** `infrastructure/env/.env` instead, so it
checks the exact credentials a live run will use:

```powershell
Set-Location tools/datasource-preflight
python preflight_infra_env.py              # all sources
python preflight_infra_env.py --only firms openaq gfw sentinelhub   # a subset
```

- **PASS** — reachable and authenticated (or anonymous + reachable).
- **SKIP** — an optional key isn't set; not required for that source.
- **FAIL on a keyed source** (FIRMS/GFW/Sentinel Hub/OpenAQ/NASA) — the credential in
  `infrastructure/env/.env` is missing or rejected. **Stop and fix it** before continuing
  (see [§1](#1-conventions--one-time-setup) for where the file lives; §10-B below for
  which env var each connector reads).
- **FAIL on "Sentinel Hub Statistical" / "TROPOMI"** can also be a non-credential,
  account-entitlement issue (trial accounts often lack the Sentinel-5P collection) —
  Sentinel-5P and MODIS AOD now default to the **free Google Earth Engine** backend
  (`Google Earth Engine` preflight check); see *Known data-availability gaps* below.

### Step 1 — Start infrastructure

```powershell
Set-Location "c:\D Drive\Projects\DE\Projects\space-data-ai-platform\infrastructure\docker"
$ALL = @('-f','docker-compose.yml','-f','docker-compose.storage.yml','-f','docker-compose.ingestion.yml',
         '-f','docker-compose.processing.yml','-f','docker-compose.observability.yml','-f','docker-compose.bi.yml',
         '--env-file','../env/.env')
docker compose @ALL --profile storage --profile core --profile bi up -d
docker compose @ALL ps    # confirm postgres/minio/iceberg-rest/kafka/spark-master/spark-worker/airflow/superset healthy
```

(See [§2](#2-start--stop-the-platform) for profile details. Skip `ai`/`obs` for a full run
unless you also need MLflow/Grafana — mind the 16 GB budget; never peak `processing` + `ai`.)

### Step 2 — Start the ingestion runner

```powershell
$REPO = "c:\D Drive\Projects\DE\Projects\space-data-ai-platform"
docker rm -f space-ingest-runner 2>$null
docker run -d --name space-ingest-runner --network space-ops-net `
  -v "${REPO}:/work" -w /work `
  -e KAFKA_BOOTSTRAP=kafka:9092 -e MINIO_ENDPOINT=http://minio:9000 `
  python:3.11-slim sleep infinity
docker exec space-ingest-runner pip install -q -r ingestion/requirements.txt
docker exec space-ingest-runner python -m ingestion.scripts.create_topics
```

See [§10](#10-running-the-ingestion-layer) for why this has to run inside the Docker network.

### Step 3 — Streaming ingestion (telemetry → Bronze → cleaned/DLQ)

```powershell
docker exec space-ingest-runner python -m ingestion.streaming.producers.telemetry_producer --max 300 --rate 200
docker exec space-ingest-runner python -m ingestion.streaming.consumers.raw_ingest_consumer --batch-size 100 --max-batches 3
docker exec space-ingest-runner python -m ingestion.streaming.consumers.validation_consumer --max 300
```

### Step 4 — Batch ingestion (every real API source, incl. climate)

[`ingestion/scripts/run_full_batch_ingest.py`](ingestion/scripts/run_full_batch_ingest.py) is the
one-shot "ingest everything now" driver (DAGs remain the canonical *scheduled*
orchestration — this is the manual full-run helper):

```powershell
docker exec space-ingest-runner python -m ingestion.scripts.run_full_batch_ingest
```

Lands SWPC, CelesTrak, NASA POWER, FIRMS, GFW, Sentinel Hub (scene metadata + NDVI
statistics), OpenAQ, TROPOMI, and MODIS/VIIRS AOD to Bronze. Real-time feeds use "now";
latency-sensitive sources (POWER/OpenAQ/Sentinel Hub statistics) use a settled
`2024-06-01..07` window to avoid upstream processing-latency 404/422s.

### Step 5 — Seed the simulation-track Bronze entities (fresh start / `down -v` only)

Bronze survives `stop`/`start` and `down`/`up`, so skip this step unless the MinIO
volume is empty:

```powershell
docker exec space-ingest-runner python -m transformation.scripts.seed_bronze_lake --records 120
$u = (Select-String '../env/.env' -Pattern '^MINIO_ROOT_USER=').Line.Split('=')[1]
$p = (Select-String '../env/.env' -Pattern '^MINIO_ROOT_PASSWORD=').Line.Split('=')[1]
foreach ($d in 'satellite_telemetry','orbit_position','space_weather') {
  docker run --rm --network space-ops-net -v "${REPO}/.bronze_seed:/seed" `
    -e MC_HOST_local="http://${u}:${p}@minio:9000" minio/mc `
    cp "/seed/$d.json" "local/bronze/$d/$d.json"
}
```

### Step 6 — Transformation: Bronze → Silver → Gold (batch, incl. climate)

```powershell
docker exec -u root space-platform-spark-master-1 bash /opt/spark/work-dir/transformation/scripts/run_pipeline.sh
```

Runs every Silver entity (sim `telemetry`/`orbit`/`space_weather` + MVP EO
`fire`/`vessel`/`scene`/`index` + climate `air_quality`/`aerosol`/`atmos_column`) one at a
time, the Spark Gold-lakehouse writer (14 marts → `s3://gold`), then the dbt-duckdb
demonstrator (`dbt deps && dbt run && dbt test`). See [§11-A](#a-batch-pipeline--bronze--silver--gold-one-command)
for expected output and the full mart list. Launch it detached (`docker exec -u root -d ...`)
and tail the log if you don't want to block the shell — first run downloads Ivy jars (~minutes).

### Step 7 — Transformation: streaming (Kafka → Silver windows)

Long-running (`awaitTermination`); launch detached. The configured window is 1 minute
with a 30-second slide and 2-minute watermark. Space the later-timestamped second wave
at least 3.5 minutes after the first, then allow 60 seconds for micro-batches to flush
append-mode windows before stopping. Because the query uses `startingOffsets=latest`,
produce the first wave only after the log reports `streaming query started`.

```powershell
docker exec -u root -d space-platform-spark-master-1 /opt/spark/bin/spark-submit `
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.9,org.apache.hadoop:hadoop-aws:3.3.4 `
  --conf spark.jars.ivy=/tmp/.ivy2 --conf spark.sql.extensions= `
  --conf spark.driver.host=localhost --conf spark.driver.bindAddress=127.0.0.1 `
  /opt/spark/work-dir/transformation/scripts/run_stream.py
# ...produce the second wave at least 3.5 min after the first; wait 60s, then:
docker exec space-platform-spark-master-1 pkill -f SparkSubmit
```

See [§11-B](#b-streaming-job--kafka--silver-windows) for details.

### Step 8 — Serving: Gold → dbt data products

```powershell
Set-Location "c:\D Drive\Projects\DE\Projects\space-data-ai-platform"
$p = (Get-Content infrastructure/env/.env | Select-String '^MINIO_ROOT_PASSWORD=' | ForEach-Object { ($_ -split '=',2)[1] })
docker run --rm --network space-data-net --user root --entrypoint bash `
  -v "${PWD}:/work" `
  -e DBT_PROFILES_DIR=/work/serving/dbt -e SERVING_DUCKDB_PATH=/work/serving/dbt/serving.duckdb `
  -e DUCKDB_S3_ENDPOINT=minio:9000 -e MINIO_ROOT_USER=platform_minio -e MINIO_ROOT_PASSWORD=$p `
  space-platform/spark-transform:3.5.9 -lc "cd /work/serving/dbt && dbt deps && dbt run && dbt test"
```

Expect `dbt run` to build every `serving_*` model + `mv_kpi_platform_daily`/`mv_kpi_climate_daily`
and `dbt test` to report `PASS=52`. Serving reads **only** `s3://gold/<table>/*.parquet`, so Step 6 must
run first. **`SERVING_DUCKDB_PATH` must point at the bind-mounted `/work/serving/dbt/serving.duckdb`**
(not a container-local `/tmp` path) — that file is the same one `bi.yml` mounts read-only into
Superset (`/opt/serving/serving_products.duckdb`), so building anywhere else leaves the BI
dashboards on stale data. See [§11-C](#c-serving-data-products--gold--dbt-products).

### Step 9 — BI: Superset

Superset (started in Step 1 via `--profile bi`) reads the persistent
`serving/dbt/serving.duckdb` file mounted read-only into the container — no extra step
needed once Step 8 has built it (with the correct `SERVING_DUCKDB_PATH`, see above). Open
**http://localhost:8089** (login `admin` / `SUPERSET_ADMIN_PASSWORD` from
`infrastructure/env/.env`, see [§5](#5-service-urls--login-guidance)) and confirm the
dashboards render with fresh numbers: Executive, Earth Observation, Air Quality & Dust,
Climate Indicators, Weather, Imagery & Catalog Quality, Simulation Track.

**First time only (or after adding new BI assets in `bi/superset/`)** — the dashboards/
datasets/charts are checked in as YAML (`bi/superset/`) but are **not** auto-imported by
`docker compose up`; import the assets-as-code bundle via the v1 API:

```powershell
# 1. Package bi/superset/ into a zip with a `bundle/` root and forward-slash entries
#    (PowerShell's Compress-Archive uses backslashes, which the importer rejects)
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::Open("$PWD/bi_bundle.zip", 'Create')
Get-ChildItem -Path bi/superset -Recurse -File | ForEach-Object {
  $rel = $_.FullName.Substring("$PWD\bi\superset\".Length) -replace '\\','/'
  $entry = $zip.CreateEntry("bundle/$rel"); $s = $entry.Open()
  $bytes = [IO.File]::ReadAllBytes($_.FullName); $s.Write($bytes, 0, $bytes.Length); $s.Close()
}
$zip.Dispose()

# 2. Log in, fetch a CSRF token (same cookie jar), then POST the bundle
'{"username":"admin","password":"<SUPERSET_ADMIN_PASSWORD>","provider":"db","refresh":true}' |
  Out-File login.json -Encoding ascii -NoNewline
$access = (curl.exe -s -c cookies.txt -X POST http://localhost:8089/api/v1/security/login `
  -H "Content-Type: application/json" --data "@login.json" | ConvertFrom-Json).access_token
$csrf = (curl.exe -s -b cookies.txt -c cookies.txt http://localhost:8089/api/v1/security/csrf_token/ `
  -H "Authorization: Bearer $access" | ConvertFrom-Json).result
curl.exe -s -b cookies.txt -X POST "http://localhost:8089/api/v1/assets/import/" `
  -H "Authorization: Bearer $access" -H "X-CSRFToken: $csrf" `
  -F "bundle=@bi_bundle.zip;type=application/zip"
# Expect {"message":"OK"}. Import is idempotent (fixed UUIDs) — safe to re-run after edits.
Remove-Item login.json, cookies.txt, bi_bundle.zip
```

See [bi/superset/README.md](bi/superset/README.md) for the full asset-import gotchas
(zip path separators, `type: assets` vs `type: Dashboard` endpoints, position_json
`chartId` requirements).

### Step 10 — Clean up

```powershell
docker rm -f space-ingest-runner
```

Infrastructure containers can stay up (`docker compose @ALL --profile all down` only when
you're done for the session — see [§2](#2-start--stop-the-platform)).

### Known data-availability gaps (not credential issues)

These do not block the run — every mart lands (even 0-row, schema-only Parquet) so
serving/BI stay contract-stable downstream.

| Source / mart | Symptom | Cause |
| --- | --- | --- |
| Sentinel-5P (TROPOMI) + MODIS/VIIRS AOD | 0 records if GEE not configured | These now use the **free Google Earth Engine** backend (`gee_s5p.py` / `gee_aod.py`) because their Sentinel Hub collections are not entitled on the free plan. Set `GEE_PROJECT` / `GEE_SERVICE_ACCOUNT` / `GEE_KEY_FILE` (see §11 preflight) to populate them |
| `fact_air_quality_daily`, `fact_dust_event_daily`, `fact_climate_indicator_daily`, `fact_vegetation_health_daily` | 0-row Gold marts | Air-quality mart populates from OpenAQ today; the AOD/trace-gas-derived marts populate once GEE is configured. Land an empty (schema-only) Parquet by design until then |
| NASA FIRMS | 0 detections sometimes | Real-time active-fire feed — genuinely no fires in the requested bbox/day |
| `kpi_flood_aoi_daily`, `kpi_launch_monthly` | 0 rows | No NDWI/launch source ingested yet; the path is fully wired end to end, just no upstream data |

---

## 13. Manual data verification & validation (per stage)

A "did it actually work?" cheat-sheet for every stage in §12, with **both** a UI way
(click around, no terminal) and a CLI/API way (scriptable, exact numbers) wherever a UI
exists. Use this after any run — full or partial — to sanity-check the data before
trusting a dashboard number.

### Quick reference

| Stage | Data lives in | UI check | CLI/API check |
| --- | --- | --- | --- |
| Batch ingestion (Bronze) | MinIO `bronze/<SOURCE>/ingest_date=…/` | MinIO Console `:9001` | `mc ls --recursive local/bronze/<SOURCE>` |
| Streaming ingestion (Kafka) | Topics `telemetry.satellite.*`, `space.weather.events`, … | Kafka UI `:8088` | `kafka-console-consumer.sh` / `kafka-get-offsets.sh` |
| Batch transformation — Silver | MinIO `silver/silver_<entity>/` | MinIO Console `:9001` | DuckDB `read_parquet('s3://silver/silver_<entity>/*.parquet')` |
| Batch transformation — Gold | MinIO `gold/<table>/` | MinIO Console `:9001` | DuckDB `read_parquet('s3://gold/<table>/*.parquet')` |
| Streaming transformation | MinIO `silver/stream_sat_health_1m/` | MinIO Console `:9001` (+ Kafka UI consumer group) | DuckDB query + `_spark_metadata` batch count |
| Serving (dbt products) | `serving/dbt/serving.duckdb` | — (Superset Explore doubles as a UI, see below) | `dbt test` output; direct DuckDB query |
| BI | Superset dashboards | Superset UI `:8089` | `POST /api/v1/chart/data` |
| Orchestration | Airflow DAG runs | Airflow UI `:8082` | `docker compose @ALL logs airflow` |

> Spark **does not** have a usable job-progress UI in this stack: `run_pipeline.sh` /
> `run_silver.py` / `run_gold.py` run in `local[*]` driver mode *inside* the `spark-master`
> container (not submitted to the standalone cluster), so they never appear as
> "Applications" on the Spark Master UI (`:8080`) — that UI only reflects the standalone
> cluster's registered workers/resources, which is still useful for confirming
> `spark-worker` is alive, just not for per-job progress. For job progress, tail the log
> file (§11) or check the output location directly (below).

### A) Batch ingestion — Bronze

**UI (MinIO Console, http://localhost:9001):** log in with `MINIO_ROOT_USER` /
`MINIO_ROOT_PASSWORD` → **Object Browser** → bucket `bronze` → click into
`<SOURCE>/ingest_date=YYYY-MM-DD/<batch_id>/`. Click a `part-0000.jsonl` object → **Preview**
to see the raw envelope JSON lines. Confirm: the folder exists for *today's* `ingest_date`,
file size is non-zero, and the object count matches what the connector logged
(`ingested N records`).

**CLI:**

```powershell
# List what landed for one source (uses the $u/$p/$MC alias from §7)
docker @MC ls --recursive local/bronze/OPENAQ

# Peek at one envelope record (first line of a part file)
docker @MC cat local/bronze/OPENAQ/ingest_date=2026-07-13/<batch_id>/part-0000.jsonl | Select-Object -First 1

# Per-source object + byte counts (same helper as §10 "Verify the run")
docker exec space-ingest-runner python -c "
import boto3; from botocore.config import Config
from ingestion.config.settings import settings as s
cl=boto3.client('s3',endpoint_url=s.minio.endpoint,aws_access_key_id=s.minio.access_key,aws_secret_access_key=s.minio.secret_key,region_name=s.minio.region,config=Config(s3={'addressing_style':'path'}))
for p in ['telemetry/','POWER/','SWPC/','CELESTRAK/','FIRMS/','GFW/','SENTINELHUB/','OPENAQ/']:
    objs=cl.list_objects_v2(Bucket='bronze',Prefix=p).get('Contents',[])
    print(p, len(objs), 'objs', sum(o['Size'] for o in objs), 'bytes')"
```

**Checklist:** object exists under `bronze/<SOURCE>/ingest_date=.../`; every JSON line has
the envelope fields `_source`, `_batch_id`, `_ingest_id`, `_event_ts`; object/record counts
match the connector's `ingested N records` log line (§10).

### B) Streaming ingestion — Kafka topics

**UI (Kafka UI, http://localhost:8088):** open a topic (e.g. `telemetry.satellite.raw`) →
**Messages** tab to browse individual payloads (filter by partition/offset, or "Newest"
first) → **Consumers** tab to see consumer-group lag (`bronze-raw-writer`,
`telemetry-validator` should show **lag = 0** once a run finishes draining the topic).
The topic's **Overview** tab shows partition count and total message count at a glance.

**CLI:**

```powershell
# End offsets (total message counts) per topic
docker compose @ALL exec -T kafka /opt/kafka/bin/kafka-run-class.sh kafka.tools.GetOffsetShell `
  --broker-list localhost:9092 --topic telemetry.satellite.cleaned --time -1

# Or, from the ingestion runner (works even if the above class was removed upstream):
docker exec space-ingest-runner python -c "
from kafka import KafkaConsumer
from kafka.structs import TopicPartition as TP
c=KafkaConsumer(bootstrap_servers='kafka:9092')
for t in ['telemetry.satellite.raw','telemetry.satellite.cleaned','telemetry.satellite.dlq']:
    ps=c.partitions_for_topic(t) or set(); tps=[TP(t,p) for p in ps]
    print(t, sum(c.end_offsets(tps).values()) if tps else 0)
c.close()"

# Tail the latest few messages by hand
docker compose @ALL exec -T kafka /opt/kafka/bin/kafka-console-consumer.sh `
  --bootstrap-server localhost:9092 --topic telemetry.satellite.cleaned --from-beginning --max-messages 5
```

**Checklist:** `telemetry.satellite.raw` end-offset increased by the amount you produced;
`cleaned` + `dlq` end-offsets sum to the same amount (validation splits, never drops);
consumer-group lag is 0 after a bounded run finishes.

### C) Batch transformation — Silver

**UI (MinIO Console):** bucket `silver` → `silver_<entity>/` (e.g. `silver_air_quality`,
`silver_telemetry`) → confirm a `_SUCCESS` marker **and** one or more
`part-*.snappy.parquet` files with a timestamp matching your run (Parquet previews as
binary in the console — use the CLI/DuckDB check below to see actual rows).

**CLI (DuckDB via httpfs, run inside `spark-master` which already has DuckDB + the repo mounted):**

```powershell
docker exec -u root space-platform-spark-master-1 python3 -c "
import duckdb
con = duckdb.connect()
con.execute(\"install httpfs; load httpfs; set s3_endpoint='minio:9000'; set s3_access_key_id='platform_minio'; set s3_secret_access_key='platform_minio_pw'; set s3_use_ssl=false; set s3_url_style='path';\")
for t in ['silver_telemetry','silver_orbit','silver_space_weather','silver_fire','silver_vessel','silver_scene','silver_index','silver_air_quality','silver_aerosol','silver_atmos_column']:
    try:
        n = con.execute(f\"select count(*) from read_parquet('s3://silver/{t}/*.parquet')\").fetchone()[0]
        print(t, n)
    except Exception as e:
        print(t, 'ERR', e)
"
```

**Checklist:** row count > 0 for entities with landed Bronze data (an absent Bronze
source is *skipped*, not an error — see §11's error table); a fresh timestamp on the
parquet parts (not left over from a previous run).

### D) Batch transformation — Gold

**UI (MinIO Console):** bucket `gold` → one folder per mart (14 total: `kpi_wildfire_aoi_daily`,
`kpi_flood_aoi_daily`, `fact_vessel_activity`, `fact_scene_catalog`, `kpi_eo_daily`,
`kpi_aoi_validation`, `ref_aoi`, `fact_air_quality_daily`, `fact_dust_event_daily`,
`fact_climate_indicator_daily`, `fact_vegetation_health_daily`, `fact_sat_health`,
`kpi_launch_monthly`, `fact_weather_impact`). Every mart lands *some* Parquet file even
with 0 rows (schema-only, ~650–2000 bytes) — a **missing folder** means the Gold job
never ran, not that the source was empty.

**CLI:**

```powershell
docker exec -u root space-platform-spark-master-1 python3 -c "
import duckdb
con = duckdb.connect()
con.execute(\"install httpfs; load httpfs; set s3_endpoint='minio:9000'; set s3_access_key_id='platform_minio'; set s3_secret_access_key='platform_minio_pw'; set s3_use_ssl=false; set s3_url_style='path';\")
marts = ['kpi_wildfire_aoi_daily','kpi_flood_aoi_daily','fact_vessel_activity','fact_scene_catalog',
         'kpi_eo_daily','kpi_aoi_validation','ref_aoi','fact_air_quality_daily','fact_dust_event_daily',
         'fact_climate_indicator_daily','fact_vegetation_health_daily','fact_sat_health',
         'kpi_launch_monthly','fact_weather_impact']
for t in marts:
    n = con.execute(f\"select count(*) from read_parquet('s3://gold/{t}/*.parquet')\").fetchone()[0]
    print(t, n)
"
```

**Checklist:** cross-check row counts against the *Known data-availability gaps* table
above (a 0-row `fact_air_quality_daily` is expected only if OpenAQ wasn't ingested; a
0-row mart you *do* expect data for means Step 6 needs a re-run — see §11's troubleshooting
table for common causes).

### E) Streaming transformation — Kafka → Silver windows

**UI:** Kafka UI's **Consumers** tab shows the streaming query's consumer group actively
committing offsets (growing, not stuck) while the job is running. There is no Spark job
UI for this driver either (see the caveat above); rely on the MinIO output + log tail.

**CLI:**

```powershell
# Batch-commit count for the streaming sink (each new file = one micro-batch commit)
docker @MC ls --recursive local/silver/stream_sat_health_1m/_spark_metadata/

# Row content of the windowed output
docker exec -u root space-platform-spark-master-1 python3 -c "
import duckdb
con = duckdb.connect()
con.execute(\"install httpfs; load httpfs; set s3_endpoint='minio:9000'; set s3_access_key_id='platform_minio'; set s3_secret_access_key='platform_minio_pw'; set s3_use_ssl=false; set s3_url_style='path';\")
print(con.execute(\"select * from read_parquet('s3://silver/stream_sat_health_1m/*.parquet') order by window_start desc limit 10\").fetchall())
"

# Tail the job log for progress / watermark advancement
docker exec space-platform-spark-master-1 tail -n 40 /tmp/run_stream.log
```

**Checklist:** `_spark_metadata` batch-id files increase roughly every `trigger_interval`
(30s default) once messages are flowing; window rows appear only after the watermark
(2 min default) passes a window's end — produce a **second**, later-timestamped wave of
telemetry if the first window looks stuck at 0 rows (see §11-B).

### F) Serving — dbt data products

**No dedicated UI** (no serving API yet — 🔜 in the Phase Status table). `dbt test`'s own
PASS/WARN/ERROR summary **is** the primary validation; treat any `ERROR` or unexpected
`FAIL` as a broken run. For ad-hoc spot-checks, query the built DuckDB file directly:

```powershell
docker run --rm --network space-data-net --user root --entrypoint bash `
  -v "${PWD}:/work" space-platform/spark-transform:3.5.9 -lc "python3 -c \"
import duckdb
con = duckdb.connect('/work/serving/dbt/serving.duckdb', read_only=True)
for t in ['serving_wildfire_daily','serving_vessel_activity','serving_scene_catalog',
          'serving_air_quality_daily','serving_dust_event_daily','serving_climate_indicator_daily',
          'serving_vegetation_health_daily']:
    print(t, con.execute(f'select count(*) from serving.{t}').fetchone()[0])
\""
```

**Checklist:** `dbt test` reports `PASS=52 WARN=0 ERROR=0`; row counts here should be
**≤** the corresponding Gold mart's row count (serving reads straight from Gold, no fan-out).

### G) BI — Superset

**UI (Superset, http://localhost:8089):** log in (`admin` / `SUPERSET_ADMIN_PASSWORD`) →
open a dashboard → confirm every chart renders (no red error banners, no perpetual
spinner) and shows non-empty data where you expect it (per the gaps table, `Weather &
Climate` charts backed by TROPOMI/AOD will legitimately be empty). To inspect the exact
query + result rows behind any chart without leaving the UI: click the chart title →
**Edit chart** → **Results** panel (bottom of Explore) shows the returned rows, and
**View query** shows the generated SQL — this is the fastest manual way to confirm a
number on a dashboard matches the underlying data. (SQL Lab's *Run* button works for
building ad-hoc queries, but its "Results backend is not configured" in this stack, so
long-running/async queries won't return — prefer the Explore **Results** panel described
above, or query DuckDB directly per §11-C/§13-F.)

**API (scriptable):**

```powershell
# Login -> access token
'{"username":"admin","password":"<SUPERSET_ADMIN_PASSWORD>","provider":"db","refresh":true}' |
  Out-File login.json -Encoding ascii -NoNewline
$access = (curl.exe -s -X POST http://localhost:8089/api/v1/security/login `
  -H "Content-Type: application/json" --data "@login.json" | ConvertFrom-Json).access_token

# List datasets / dashboards actually imported
curl.exe -s "http://localhost:8089/api/v1/dataset/?q=(page_size:100)" -H "Authorization: Bearer $access" |
  python -c "import json,sys; d=json.load(sys.stdin); print(sorted(r['table_name'] for r in d['result']))"
curl.exe -s "http://localhost:8089/api/v1/dashboard/?q=(page_size:100)" -H "Authorization: Bearer $access" |
  python -c "import json,sys; d=json.load(sys.stdin); print([(r['id'],r['dashboard_title']) for r in d['result']])"

# Row count through a dataset (id N from the list above), bypassing the chart UI entirely
'{"datasource":{"id":N,"type":"table"},"queries":[{"columns":[],"metrics":[{"expressionType":"SQL","label":"cnt","sqlExpression":"COUNT(*)"}],"row_limit":10}],"result_format":"json","result_type":"full"}' |
  Out-File chart_query.json -Encoding ascii -NoNewline
curl.exe -s -X POST "http://localhost:8089/api/v1/chart/data" -H "Authorization: Bearer $access" `
  -H "Content-Type: application/json" --data "@chart_query.json"
Remove-Item login.json, chart_query.json
```

**Checklist:** dataset/dashboard lists include everything you expect (if new BI assets
were added but never imported, see the import snippet in §12 Step 9); `chart/data`
returns `"status": "success"` with a non-zero `cnt` for datasets you expect to be
populated.

---

## 14. Airflow-orchestrated pipelines & run-logging (`pipelines/`)

Everything in §12 can also be run **from Airflow** instead of by hand, with automatic
run/row-level logging to PostgreSQL. This is a thin orchestration layer over the exact
same commands documented in §10/§11/§12 — it doesn't change what runs, only *how it's
triggered* and *what gets recorded*.

### What it is

- **3 DAGs**, no schedule (manual trigger only — see the table in §5):
  `platform_batch_pipeline` (ingestion → transformation → serving → bi),
  `platform_streaming_pipeline` (bounded streaming demo), and
  `platform_master_pipeline` (triggers the batch pipeline fully, then the streaming one).
- **`metadata` schema in PostgreSQL** (ADR-007's already-reserved "lineage/quality"
  schema) gets 12 run-logging tables: a header table per stage
  (`ingestion_run`, `transformation_run`, `serving_run`, `bi_run`, `streaming_run`, plus
  the roll-ups `batch_run`/`master_run`) and a detail table per stage with one row **per
  source / Silver entity / Gold mart / serving model / BI dataset** processed in that
  run (`ingestion_run_detail`, `transformation_run_detail`, `serving_run_detail`,
  `bi_run_detail`, `streaming_run_detail`). `run_id` is Airflow's own `dag_run_id`,
  threaded through every table so one run's whole trail is queryable by a single value;
  `parent_run_id` links a child run (e.g. the batch DAG run `platform_master_pipeline`
  triggered) back to its trigger. Every write is idempotent (`INSERT ... ON CONFLICT DO
  UPDATE`), so a retried task never duplicates a row.
- Defined in the new top-level `pipelines/` package: `pipelines/dags/*.py` (the 3 DAGs,
  bind-mounted into Airflow at `/opt/airflow/dags/pipelines`), `pipelines/common/*.py`
  (the shared `StageRunLogger`, DuckDB-httpfs row-counters, Superset REST client),
  `pipelines/config/settings.py`. Offline-testable: `pipelines/tests/` (10 unit tests,
  no real Postgres needed) — run with `cd pipelines; python -m pytest`.
- The migration lives at `infrastructure/configs/postgres/init/02-pipeline-run-logging.sql`
  (auto-applied on a fresh volume; also wired into `bootstrap.sh` step 3b for existing ones).

### Trigger a run

```powershell
# From the CLI (or use the ▶ Trigger DAG button in the UI, see §5)
docker compose @ALL exec airflow airflow dags trigger platform_batch_pipeline
docker compose @ALL exec airflow airflow dags trigger platform_streaming_pipeline
docker compose @ALL exec airflow airflow dags trigger platform_master_pipeline   # runs both, sequentially
```

Each returns immediately with a `dag_run_id` like `manual__2026-07-20T12:37:27+00:00`
(the master DAG's triggered children get a derived id: `<run_id>__batch` /
`<run_id>__streaming`) — use that value in the queries below.

### Monitor progress (UI or CLI)

```powershell
# UI: http://localhost:8082 -> click the DAG -> Grid view (per-task status/logs)

# CLI: all task states for one run
docker compose @ALL exec airflow airflow tasks states-for-dag-run platform_batch_pipeline "<dag_run_id>"

# CLI: just the DAG run's overall state
docker compose @ALL exec airflow airflow dags list-runs --dag-id platform_batch_pipeline
```

### Query run history (the actual point of this layer)

```powershell
# Every batch pipeline run, most recent first, with total rows processed
docker compose @ALL exec -T postgres psql -U platform -d platform -c `
  "select run_id, status, duration_seconds, total_rows, error_message from metadata.batch_run order by started_at desc limit 10;"

# Per-source ingestion detail for one run (status/rows/error per source)
docker compose @ALL exec -T postgres psql -U platform -d platform -c `
  "select unit_name, status, rows, error_message from metadata.ingestion_run_detail where run_id='<dag_run_id>' order by started_at;"

# Per-entity/mart transformation detail (Silver row counts, Gold mart row counts)
docker compose @ALL exec -T postgres psql -U platform -d platform -c `
  "select unit_name, status, rows from metadata.transformation_run_detail where run_id='<dag_run_id>' order by started_at;"

# Per-model serving detail, per-dataset BI-refresh detail, per-unit streaming detail — same pattern:
docker compose @ALL exec -T postgres psql -U platform -d platform -c `
  "select unit_name, status, rows, error_message from metadata.serving_run_detail where run_id='<dag_run_id>';"
docker compose @ALL exec -T postgres psql -U platform -d platform -c `
  "select unit_name, status, error_message from metadata.bi_run_detail where run_id='<dag_run_id>';"
docker compose @ALL exec -T postgres psql -U platform -d platform -c `
  "select unit_name, status, rows from metadata.streaming_run_detail where run_id='<dag_run_id>';"

# A master run's rollup, incl. which batch/streaming run_ids it triggered
docker compose @ALL exec -T postgres psql -U platform -d platform -c `
  "select run_id, status, batch_run_id, streaming_run_id, error_message from metadata.master_run order by started_at desc limit 5;"
```

**Checklist:** a `FAILED` detail row always has a non-null `error_message` (real
exception text, not just a status flag); a stage's header row's `total_rows`/`total_units`
equal the `sum(rows)`/`count(*)` of its own detail rows for that `run_id`; `batch_run`'s
`total_rows` equals the sum across its 4 stage headers for that run.

| Symptom | Likely cause / fix |
| --- | --- |
| A task is `up_for_retry` / `failed` right after you fixed something (env var, schema, code) | Airflow does not auto-retry a task just because you fixed the underlying cause — clear it explicitly: `airflow tasks clear -y -t <task_id> -s <exec_date> -e <exec_date> <dag_id>`. If a **downstream** task already shows `upstream_failed`, clear that one too (clearing the upstream alone does not reschedule it). |
| `ModuleNotFoundError: No module named 'kafka.vendor.six.moves'` in a streaming task | `kafka-python==2.0.2`'s vendored `six` shim breaks under Airflow's Python 3.12. Already fixed via `pipelines/common/kafka_py312_shim.py` (imported for its side effect at the top of `streaming_pipeline_dag.py`) — if you see this again, confirm that import is still first in the file. |
| 10 Silver tasks all show `running` at once and the `spark-master` container hits ~100% of its `mem_limit` | A DAG's Silver-entity tasks were built as a plain list without explicit `>>` chaining, so Airflow's LocalExecutor ran them all concurrently against the one Spark driver. Both `transformation_medallion_batch` and `platform_batch_pipeline`'s transformation stage now chain every entity `previous >> next` — if you add a new entity, chain it into that sequence, never as a bare parallel task. |
| `platform_batch_pipeline` looks "stuck" for 20-40 minutes | Expected — it's making real API calls (TROPOMI/MODIS_AOD via Earth Engine, OpenAQ, Sentinel Hub) and running 10 Spark jobs sequentially. Check `metadata.ingestion_run_detail` / `transformation_run_detail` (above) to see live per-unit progress instead of waiting on the UI. |

---

## Phase Status & Changelog

What is operationally available today, and what each future phase will add to this runbook.

| Phase | Adds to this runbook | Status |
| --- | --- | --- |
| 04 / 07 — Infrastructure | Start/stop, status, URLs, PostgreSQL & MinIO access, Kafka basics, lakehouse query *mechanisms* | ✅ Available |
| 08 — Ingestion | §10 runner pattern; live Kafka topics + offset checks; synthetic streaming pipeline; API connectors → Bronze; Bronze object inspection | ✅ Available |
| 09 — Transformation | §11 one-command Bronze→Silver→Gold pipeline (hardened `spark-master` image with dbt baked in); sim + MVP Earth-observation Silver entities; Spark Gold-lakehouse writer materialising all ten marts to `s3://gold` (the serving source, with the Copernicus-EMS AOI seed); Kafka→Silver structured streaming | ✅ Available |
| 11 — Serving | Serving dbt data products (wildfire/flood/vessel/scene/AOI-validation + platform KPI MV) built from `s3://gold` Parquet via DuckDB+httpfs; `dbt run` + 18 contract tests | ✅ Data products available (FastAPI 🔜) |
| 8b / 9b / 12b — Climate/dust/air-quality track | §12 full-run recipe incl. climate connectors (OpenAQ, TROPOMI, MODIS/VIIRS AOD) and climate Gold marts/BI dashboards; `preflight_infra_env.py` + `run_full_batch_ingest.py` operator scripts | ✅ Available (TROPOMI/AOD data-availability gaps — see §12) |
| Manual verification | §13 per-stage validation cheat-sheet (Bronze/Kafka/Silver/Gold/streaming/serving/BI), UI + CLI/API methods for each | ✅ Available |
| Orchestration (`pipelines/`) | §14 Airflow-triggered `platform_batch_pipeline` / `platform_streaming_pipeline` / `platform_master_pipeline` DAGs (no schedule, manual only) + `metadata.*` run/row-level logging tables in PostgreSQL | ✅ Available |
| AI/ML | MLflow experiment/run queries; Feast feature retrieval; model registry commands | 🔜 Add MLflow section |
| RAG / LLM | Qdrant collection queries; Ollama model pull/run; Open WebUI usage | 🔜 Add LLM section |
| Serving (API) | FastAPI endpoints, auth, example requests | 🔜 Add API section |
| Observability | Grafana dashboards, Prometheus queries, alert checks | 🔜 Expand §3 |

> **Keep this current:** when a phase adds a runnable component, add its start command,
> URL/credentials, and a "how to query it yourself" snippet to the matching section above.
