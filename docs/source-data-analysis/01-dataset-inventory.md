# 01 Dataset Inventory

## Executive Summary

This inventory expands the Phase 2 catalog (30 sources) into a full source-data analysis baseline of **45 datasets and APIs** grouped into the eight prompt-defined categories. Every entry is free and open (some require free registration) and feasible on a 16 GB RAM laptop with Docker. This document is the authoritative source list; deep profiling, structure, quality, and prioritization follow in companion documents.

## Inventory Summary

| Category | Count | Primary Platform Role |
| --- | --- | --- |
| 1. Satellite Telemetry | 5 | Live position, health, beacon, and pass context |
| 2. Earth Observation | 8 | Imagery and fire/flood/change products |
| 3. Space Weather | 6 | Solar, geomagnetic, and radiation drivers |
| 4. Orbital Mechanics | 6 | Catalogs, TLE/GP, conjunctions, ephemerides |
| 5. Launch | 4 | Schedules, providers, vehicles, outcomes |
| 6. Astronomical | 5 | NEOs, bodies, minor planets, sky content |
| 7. Environmental & Climate | 8 | Weather, climate, air quality, forest, ocean |
| 8. Simulation | 3 | Synthetic telemetry and orbit generation |
| **Total** | **45** | — |

---

## 1. Satellite Telemetry Data

| # | Dataset / API | Org | Type | Volume |
| --- | --- | --- | --- | --- |
| 1 | N2YO Tracking API | N2YO | API | Small |
| 2 | Open Notify ISS Position | Open Notify | API | Small |
| 3 | ISS Lightstreamer Telemetry | NASA / ISS Mimic | Stream | Small |
| 4 | SatNOGS DB + Network | Libre Space | API | Small-Med |
| 5 | CelesTrak SatCat (status) | CelesTrak | API/File | Small |

## 2. Earth Observation Data

| # | Dataset / API | Org | Type | Volume |
| --- | --- | --- | --- | --- |
| 6 | Sentinel-2 | ESA Copernicus | API/Bulk | Large |
| 7 | Sentinel-1 SAR | ESA Copernicus | API/Bulk | Large |
| 8 | Landsat 8/9 | USGS/NASA | API/Bulk | Large |
| 9 | NASA FIRMS active fire | NASA | API/File | Small-Med |
| 10 | MODIS Terra/Aqua | NASA LP DAAC | Bulk/API | Med-Large |
| 11 | VIIRS active fire | NASA/NOAA | API/File | Small-Med |
| 12 | Copernicus EMS | ESA | File | Medium |
| 13 | Sentinel Hub Stat/Process API | Sentinel Hub | API | Small |

## 3. Space Weather Data

| # | Dataset / API | Org | Type | Volume |
| --- | --- | --- | --- | --- |
| 14 | NOAA SWPC products | NOAA | API/JSON | Small |
| 15 | NASA DONKI | NASA | API/JSON | Small |
| 16 | GOES X-ray flux | NOAA | API/JSON | Small |
| 17 | Kp / planetary index (GFZ) | GFZ Potsdam | File/API | Small |
| 18 | OMNIWeb solar wind | NASA SPDF | API/File | Small-Med |
| 19 | DSCOVR / ACE real-time | NOAA | API/JSON | Small |

## 4. Orbital Mechanics Data

| # | Dataset / API | Org | Type | Volume |
| --- | --- | --- | --- | --- |
| 20 | CelesTrak TLE/GP | CelesTrak | API/File | Small |
| 21 | Space-Track catalog | USSPACECOM | API | Small-Med |
| 22 | CelesTrak SOCRATES conjunctions | CelesTrak | File | Small |
| 23 | JPL Horizons ephemerides | NASA JPL | API/File | Small |
| 24 | NASA GCN/CCSDS OEM samples | NASA | File | Small |
| 25 | TLE history archives | CelesTrak/space-track | File | Medium |

## 5. Launch Data

| # | Dataset / API | Org | Type | Volume |
| --- | --- | --- | --- | --- |
| 26 | Launch Library 2 | The Space Devs | API | Small |
| 27 | SpaceX public data | Community | API | Small |
| 28 | RocketLaunch.Live | RocketLaunch | API | Small |
| 29 | NASA spaceflight reference | NASA | File | Small |

## 6. Astronomical Data

| # | Dataset / API | Org | Type | Volume |
| --- | --- | --- | --- | --- |
| 30 | NASA NeoWs (NEO) | NASA | API | Small |
| 31 | NASA APOD | NASA | API | Small |
| 32 | Minor Planet Center | IAU | File/API | Small-Med |
| 33 | JPL Small-Body Database | NASA JPL | API | Small |
| 34 | Heavens-Above pass data | Community | File | Small |

## 7. Environmental & Climate Data

| # | Dataset / API | Org | Type | Volume |
| --- | --- | --- | --- | --- |
| 35 | NASA POWER | NASA | API | Small |
| 36 | ERA5 (Copernicus CDS) | ECMWF | API/Bulk | Large |
| 37 | CAMS atmosphere | ECMWF | API/Bulk | Large |
| 38 | NOAA Climate Data Online | NOAA NCEI | API/Bulk | Medium |
| 39 | Global Forest Watch | WRI | API/Bulk | Medium |
| 40 | OpenAQ air quality | OpenAQ | API | Small-Med |
| 41 | NOAA tides & currents | NOAA | API | Small |
| 42 | OISST sea surface temp | NOAA | Bulk | Medium |

## 8. Simulation Data

| # | Dataset / API | Org | Type | Volume |
| --- | --- | --- | --- | --- |
| 43 | NASA SMAP/telemetry anomaly dataset | NASA | File | Small-Med |
| 44 | Synthetic telemetry (sgp4-generated) | Self | Generated | Small |
| 45 | Open Notify ISS (streaming sim source) | Open Notify | API | Small |

---

## Coverage Confirmation

- Total datasets: **45** (exceeds 30-50 requirement).
- All eight prompt categories populated.
- All sources free, open, and laptop-feasible.

## Cross References

- Detailed profiling: [02-dataset-profiling.md](./02-dataset-profiling.md)
- Phase 2 catalog: [../domain-research/02-dataset-catalog.md](../domain-research/02-dataset-catalog.md)
