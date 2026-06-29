# 08 Freshness Strategy

## Executive Summary

Datasets are classified by freshness tier to inform downstream cadence. This separates real-time, near real-time, daily batch, and static sources and explains analytics impact.

## Freshness Tiers

| Tier | Datasets | Cadence | Analytics Impact |
| --- | --- | --- | --- |
| Real-time | ISS, N2YO, SWPC, GOES, AIS | Seconds-minutes | Live dashboards, alerting |
| Near real-time | FIRMS, VIIRS, OpenAQ, EMS | <3 hr / event | Early detection |
| Daily batch | Sentinel, POWER, MODIS, GFW, OISST | Daily-weekly | Trend/change analytics |
| Lagged | ERA5, CAMS | ~5 day | Reanalysis, training |
| Static | TLE history, anomaly dataset, NASA reference | Rare | Baselines, models |

## Impact

- Real-time feeds drive streaming and alerts.
- Daily batch feeds drive Bronze→Gold trend products.
- Lagged feeds suit model training, not live ops.

## Cross References

- Relationships: [07-data-relationships.md](./07-data-relationships.md)
- Risks: [09-data-risks.md](./09-data-risks.md)
