# 03 Data Flow Analysis

## Executive Summary

This document explains how data physically and logically flows through the space data ecosystem, from spacecraft acquisition to operational decision-making on our platform. It uses Mermaid diagrams to make each flow explicit so that a data engineering team can later identify ingestion boundaries, latency expectations, and integration points. The analysis covers five flows: satellite telemetry to ground, Earth observation imagery processing, orbit prediction computation, space weather generation, and launch data recording.

## Flow 1 - Satellite Telemetry from Space to Ground

Satellites store acquired data onboard until they pass over a ground station within line of sight. During the pass, the satellite downlinks data over a radio-frequency channel. The ground station forwards raw Level 0 data to a mission operations center, which routes it to processing centers and ultimately to open archives.

```mermaid
sequenceDiagram
    participant SAT as Satellite Payload
    participant OBC as Onboard Storage
    participant GS as Ground Station
    participant MOC as Mission Operations
    participant ARC as Open Data Archive
    SAT->>OBC: Acquire and buffer sensor data
    OBC->>GS: Downlink during visible pass
    GS->>MOC: Forward Level 0 packets
    MOC->>MOC: Quality check and cataloging
    MOC->>ARC: Publish processed products
    ARC-->>GS: Pass schedules and telemetry health
```

**Key engineering implications:** data is not continuous; it arrives in bursts tied to orbital passes. Latency from acquisition to public availability ranges from hours to a few days depending on the mission.

## Flow 2 - Earth Observation Imagery Processing

Raw optical or radar measurements are corrected, calibrated, and converted into analysis-ready products. Derived products such as active fire detections or flood masks are then generated from the corrected imagery.

```mermaid
flowchart TD
    A[Level 0 Raw Sensor Data] --> B[Level 1 Radiometric and Geometric Correction]
    B --> C[Level 2 Atmospheric Correction Surface Reflectance]
    C --> D[Level 3 Gridded Composites]
    C --> E[Derived Products]
    E --> E1[Active Fire Detections]
    E --> E2[Flood Water Masks]
    E --> E3[Change Detection Layers]
    D --> F[Open Data Archive]
    E1 --> F
    E2 --> F
    E3 --> F
    F --> G[Platform Ingestion Bronze Layer]
```

**Key engineering implications:** we prefer to ingest Level 2 and derived Level 4 products to avoid heavy on-laptop scene processing. Optical products are cloud-affected; SAR products (Sentinel-1) are weather-independent and valuable for flood detection.

## Flow 3 - Orbit Prediction Computation

Orbit prediction uses tracking observations to fit an orbital model. The model is published as Two-Line Element sets (TLEs) or General Perturbations (GP) data and propagated forward to predict future positions.

```mermaid
flowchart LR
    A[Radar and Optical Tracking] --> B[Orbit Determination]
    B --> C[TLE / GP Catalog]
    C --> D[SGP4 Propagation]
    D --> E[Predicted Positions and Passes]
    E --> F[Platform Use: Revisit and Geometry Context]
```

**Key engineering implications:** TLEs are small text records updated multiple times per day. They are cheap to ingest and enable revisit-timing and acquisition-geometry context for imagery.

## Flow 4 - Space Weather Data Generation

Space weather data originates from solar observatories and in-situ sensors. Observations are converted into indices and alerts distributed through public services.

```mermaid
flowchart LR
    A[Solar Observatories GOES] --> B[X-ray Flux and Imagery]
    C[Solar Wind Sensors] --> D[Plasma and Magnetic Field]
    B --> E[Space Weather Prediction Center]
    D --> E
    E --> F[Indices Alerts and Forecasts]
    F --> G[Public APIs SWPC DONKI]
    G --> H[Platform Ingestion Future Expansion]
```

**Key engineering implications:** lightweight JSON feeds, easy to ingest, but secondary to the EO-centric MVP. Reserved for roadmap expansion.

## Flow 5 - Launch Data Recording

Launch data is compiled from agency announcements, vehicle telemetry, and post-launch outcome records, then aggregated by community and commercial APIs.

```mermaid
flowchart LR
    A[Launch Provider Schedules] --> B[Aggregator APIs]
    C[Vehicle Telemetry] --> D[Outcome Records]
    D --> B
    B --> E[Launch Library 2 / Provider APIs]
    E --> F[Platform Ingestion Optional Context]
```

**Key engineering implications:** event-driven and sparse. Useful only as contextual reference, consistent with the Phase 1 decision to exclude launch analytics from the MVP.

## Consolidated Platform Ingestion View

```mermaid
flowchart TD
    subgraph Sources
        S1[Sentinel-2 Optical]
        S2[Sentinel-1 SAR]
        S3[NASA FIRMS Fire]
        S4[AIS Vessel Tracks]
        S5[CelesTrak TLE]
        S6[NOAA SWPC]
    end
    S1 --> B[Bronze Raw]
    S2 --> B
    S3 --> B
    S4 --> B
    S5 --> B
    S6 --> B
    B --> SV[Silver Cleaned and Conformed]
    SV --> G[Gold Analytics Ready]
    G --> AI[AI / ML and Alerting]
    AI --> U[Analysts and Decision Makers]
```

## Cross References

- Source inventory is documented in [02-dataset-catalog.md](./02-dataset-catalog.md).
- Classification of these flows is in [04-data-classification.md](./04-data-classification.md).
- Quality risks per flow are in [05-data-quality-assessment.md](./05-data-quality-assessment.md).
