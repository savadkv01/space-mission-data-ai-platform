# DAG Structure

| DAG | Tasks | Code |
| --- | --- | --- |
| `ingest_nasa_firms` | per-region fire pulls | [dags/nasa_firms_ingest_dag.py](dags/nasa_firms_ingest_dag.py) |
| `ingest_noaa_swpc` | Kp snapshot | [dags/noaa_swpc_ingest_dag.py](dags/noaa_swpc_ingest_dag.py) |
| `ingest_celestrak_tle` | per-group TLE | [dags/celestrak_tle_ingest_dag.py](dags/celestrak_tle_ingest_dag.py) |
| `ingest_nasa_power` | per-point weather | [dags/nasa_power_ingest_dag.py](dags/nasa_power_ingest_dag.py) |

Each task is a `PythonOperator` calling `run_connector_to_bronze`. DAGs guard the Airflow import so they remain importable/lint-clean without Airflow installed.

Narrative: [docs/ingestion/03-batch-design.md](../../docs/ingestion/03-batch-design.md).
