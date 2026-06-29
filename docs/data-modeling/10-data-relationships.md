# 10 - Data Relationships

> **Phase 6 - Data Modeling** · Document 10 of 18

## Core Relationships

| Relationship | Cardinality |
| --- | --- |
| Satellite ↔ Mission | many-to-one |
| Satellite ↔ Telemetry | one-to-many |
| Launch ↔ Satellite | one-to-many |
| Space weather ↔ Telemetry anomalies | one-to-many |
| Earth observation ↔ Climate events | many-to-many |

## ER Diagram

```mermaid
erDiagram
    dim_mission ||--o{ dim_satellite : has
    dim_satellite ||--o{ ts_telemetry : emits
    fact_launch ||--o{ dim_satellite : deploys
    dim_storm ||--o{ fact_weather_impact : drives
    dim_satellite ||--o{ fact_weather_impact : affected
    fact_fire_detection }o--o{ dim_geo : observes
    dim_geo ||--o{ fact_flood_extent : covers
```

## Cross References

- [03-silver-layer.md](03-silver-layer.md) · [05-star-schemas.md](05-star-schemas.md)
