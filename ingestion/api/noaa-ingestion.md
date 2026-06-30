# NOAA Ingestion

Narrative: [docs/ingestion/04-api-ingestion.md](../../docs/ingestion/04-api-ingestion.md).

| Source | Connector | Auth | Notes |
| --- | --- | --- | --- |
| NOAA SWPC planetary K-index | [noaa_swpc.py](noaa_swpc.py) | anonymous | first row is header → zipped into records; `_event_ts` from `time_tag` |

Can run as a batch DAG ([batch/dags/noaa_swpc_ingest_dag.py](../batch/dags/noaa_swpc_ingest_dag.py)) or as a streaming bridge ([streaming/producers/api_bridge_producer.py](../streaming/producers/api_bridge_producer.py) → `space.weather.events`).
