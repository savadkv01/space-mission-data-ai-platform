# NASA Ingestion

Connectors for NASA sources. Narrative: [docs/ingestion/04-api-ingestion.md](../../docs/ingestion/04-api-ingestion.md).

| Source | Connector | Auth | Notes |
| --- | --- | --- | --- |
| FIRMS / VIIRS active fire | [nasa_firms.py](nasa_firms.py) | `FIRMS_MAP_KEY` | CSV; bbox + day window; extracts `_event_ts` from acq_date/time |
| POWER daily weather | [nasa_power.py](nasa_power.py) | anonymous | flattens nested params → one record per (date, param) |

Both extend [base.py](base.py) and run on the resilient client [common/http.py](../common/http.py). Verified accessible via [tools/datasource-preflight](../../tools/datasource-preflight/).
