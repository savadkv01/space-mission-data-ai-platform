# 02 Dataset Catalog

## Executive Summary

This catalog documents 30 real-world open datasets and APIs relevant to the Space Mission Data & AI Platform. Each entry is described with its organization, data type, purpose, sample fields, update frequency, historical depth, local feasibility, and mapping to Phase 1 business problems. All sources are free and openly accessible (some require free registration). The catalog is organized into eight categories aligned with the Phase 2 task structure and prioritizes Earth observation, environmental, orbital, and maritime feeds that directly support the MVP scope.

## How to Read This Catalog

- **Type:** API, File download, Streaming, or Bulk dataset.
- **Volume:** Small (megabytes per pull), Medium (hundreds of MB), Large (multi-GB scenes).
- **MVP Relevance:** maps to Phase 1 use cases UC-15 wildfire, UC-16 flood, UC-18 illegal fishing, UC-27 disaster damage, UC-14 change detection, UC-25 metadata quality.

## Category Summary

| Category | Datasets | Primary MVP Value |
| --- | --- | --- |
| 1. Satellite Data | 4 | Imagery foundation for all EO use cases |
| 2. Earth Observation | 6 | Fire, flood, change detection products |
| 3. Space Weather | 3 | Future expansion |
| 4. Orbital / Trajectory | 3 | Acquisition geometry and revisit context |
| 5. Launch Data | 2 | Contextual reference only |
| 6. Astronomical Data | 3 | Future expansion and enrichment |
| 7. Climate / Environmental | 6 | Fire risk, flood, drought, emissions context |
| 8. Real-time Telemetry APIs | 3 | Maritime detection and live context |

---

## 1. Satellite Data

### 1.1 Copernicus Sentinel-2

- **Organization:** ESA / Copernicus (via Copernicus Data Space Ecosystem)
- **Type:** API + Bulk dataset
- **Purpose:** High-resolution optical multispectral imagery (10-60 m) for wildfire, flood, change detection, and damage assessment.
- **Sample Fields:** tile_id, acquisition_datetime, cloud_cover, band reflectances (B02-B12), geometry footprint, processing_level
- **Update Frequency:** ~5-day global revisit
- **Historical Depth:** 2015-present
- **Volume:** Large (scenes are multi-hundred MB to GB)
- **MVP Relevance:** UC-14, UC-15, UC-16, UC-27 — core optical imagery source

### 1.2 Copernicus Sentinel-1 (SAR)

- **Organization:** ESA / Copernicus
- **Type:** API + Bulk dataset
- **Purpose:** Synthetic Aperture Radar imaging that penetrates clouds and works day or night, ideal for flood mapping.
- **Sample Fields:** scene_id, acquisition_datetime, polarization (VV/VH), orbit_direction, backscatter, geometry
- **Update Frequency:** ~6-12 day revisit
- **Historical Depth:** 2014-present
- **Volume:** Large
- **MVP Relevance:** UC-16 flood (weather-independent), UC-27 damage

### 1.3 Landsat 8/9

- **Organization:** USGS / NASA
- **Type:** API + Bulk dataset (USGS EarthExplorer, AWS Open Data)
- **Purpose:** Long-baseline optical imagery (30 m) for change detection and historical comparison.
- **Sample Fields:** scene_id, path, row, acquisition_date, cloud_cover, band reflectances, thermal bands
- **Update Frequency:** ~16-day revisit
- **Historical Depth:** Landsat program 1972-present; Landsat 8 from 2013
- **Volume:** Large
- **MVP Relevance:** UC-14 change detection, UC-15 fire thermal context

### 1.4 NASA GIBS / Worldview

- **Organization:** NASA EOSDIS
- **Type:** API (WMTS/WMS tiles)
- **Purpose:** Pre-rendered global imagery tiles for rapid visualization and quick-look layers.
- **Sample Fields:** layer_id, date, tile_matrix, bbox, format
- **Update Frequency:** Daily (near real-time layers available)
- **Historical Depth:** Varies by layer, many from 2000s
- **Volume:** Small to Medium (tiles)
- **MVP Relevance:** UC-15, UC-16, UC-27 — fast visualization and dashboards

---

## 2. Earth Observation

### 2.1 NASA FIRMS (Active Fire)

- **Organization:** NASA (Fire Information for Resource Management System)
- **Type:** API + File (CSV/GeoJSON)
- **Purpose:** Near real-time active fire and thermal anomaly detections from MODIS and VIIRS.
- **Sample Fields:** latitude, longitude, brightness, scan, track, acq_date, acq_time, satellite, confidence, frp
- **Update Frequency:** Near real-time (within ~3 hours)
- **Historical Depth:** 2000-present (MODIS), 2012-present (VIIRS)
- **Volume:** Small to Medium (point records)
- **MVP Relevance:** UC-15 wildfire detection — primary feed

### 2.2 MODIS (Terra/Aqua)

- **Organization:** NASA LP DAAC
- **Type:** Bulk dataset + API
- **Purpose:** Daily moderate-resolution imagery and products (burned area, surface reflectance, land surface temperature).
- **Sample Fields:** product_id, tile, date, NDVI, burned_area, LST, quality_flags
- **Update Frequency:** Daily
- **Historical Depth:** 2000-present
- **Volume:** Medium to Large
- **MVP Relevance:** UC-15 fire progression, UC-17 drought context

### 2.3 VIIRS Active Fire

- **Organization:** NASA / NOAA (Suomi NPP, NOAA-20)
- **Type:** API + File
- **Purpose:** Higher-resolution (375 m) active fire detections complementing MODIS.
- **Sample Fields:** latitude, longitude, bright_ti4, frp, confidence, acq_date, daynight
- **Update Frequency:** Near real-time
- **Historical Depth:** 2012-present
- **Volume:** Small to Medium
- **MVP Relevance:** UC-15 wildfire detection and progression

### 2.4 Copernicus Emergency Management Service (EMS)

- **Organization:** ESA / Copernicus
- **Type:** File download (vector + raster)
- **Purpose:** Rapid mapping products for floods, fires, and disasters, including delineation and grading maps.
- **Sample Fields:** activation_id, event_type, aoi, observation_date, damage_grade, geometry
- **Update Frequency:** Event-driven
- **Historical Depth:** 2012-present
- **Volume:** Medium
- **MVP Relevance:** UC-16 flood, UC-27 damage assessment — reference and validation labels

### 2.5 NASA Earthdata (LP DAAC / Earthdata Search)

- **Organization:** NASA EOSDIS
- **Type:** API + Bulk dataset
- **Purpose:** Unified discovery and access to NASA EO products across many missions.
- **Sample Fields:** granule_id, collection, temporal_extent, spatial_extent, data_url
- **Update Frequency:** Varies by product
- **Historical Depth:** Decades depending on collection
- **Volume:** Medium to Large
- **MVP Relevance:** UC-14, UC-15, UC-25 — discovery and metadata foundation

### 2.6 Sentinel Hub Statistical / Process API

- **Organization:** Sentinel Hub (Copernicus-backed, free tier)
- **Type:** API
- **Purpose:** On-demand extraction of indices (NDVI, NDWI, NBR) for an area of interest without downloading full scenes.
- **Sample Fields:** aoi, time_range, index_value, statistics, sample_count
- **Update Frequency:** On-demand against archive
- **Historical Depth:** Matches Sentinel archive (2015-present)
- **Volume:** Small (aggregated outputs)
- **MVP Relevance:** UC-14 change detection, UC-15 burn severity, UC-17 drought — laptop-friendly extraction

---

## 3. Space Weather

### 3.1 NOAA SWPC

- **Organization:** NOAA Space Weather Prediction Center
- **Type:** API (JSON)
- **Purpose:** Solar wind, geomagnetic (Kp), and X-ray flux data plus alerts and forecasts.
- **Sample Fields:** time_tag, kp_index, bz, solar_wind_speed, xray_flux_class
- **Update Frequency:** Real-time (minutes)
- **Historical Depth:** Years of archived indices
- **Volume:** Small
- **MVP Relevance:** Future expansion (Phase 1 Tier 3, UC-21)

### 3.2 NASA DONKI

- **Organization:** NASA (Space Weather Database of Notifications, Knowledge, Information)
- **Type:** API (JSON)
- **Purpose:** Records of solar flares, coronal mass ejections, and geomagnetic storms.
- **Sample Fields:** event_id, event_type, start_time, class_type, source_location
- **Update Frequency:** Event-driven
- **Historical Depth:** ~2010-present
- **Volume:** Small
- **MVP Relevance:** Future expansion (UC-21)

### 3.3 GOES X-ray Flux

- **Organization:** NOAA
- **Type:** API (JSON)
- **Purpose:** Continuous solar X-ray flux for flare classification.
- **Sample Fields:** time_tag, flux, energy_band, satellite
- **Update Frequency:** Real-time (1 minute)
- **Historical Depth:** Multi-year archive
- **Volume:** Small
- **MVP Relevance:** Future expansion (UC-21)

---

## 4. Orbital / Trajectory Data

### 4.1 CelesTrak (TLE / GP)

- **Organization:** CelesTrak
- **Type:** API + File (text/JSON)
- **Purpose:** Two-Line Element sets and General Perturbations data for active satellites.
- **Sample Fields:** norad_id, object_name, epoch, inclination, eccentricity, mean_motion, raan
- **Update Frequency:** Multiple times daily
- **Historical Depth:** Current catalog (historical via archives)
- **Volume:** Small
- **MVP Relevance:** UC-14, UC-15 — revisit timing and acquisition geometry context

### 4.2 Space-Track (Open Subset)

- **Organization:** US Space Command (registration required, free)
- **Type:** API
- **Purpose:** Authoritative satellite catalog, TLE history, and decay/reentry data.
- **Sample Fields:** norad_cat_id, tle_line1, tle_line2, object_type, launch_date, decay_date
- **Update Frequency:** Multiple times daily
- **Historical Depth:** Full satellite catalog history
- **Volume:** Small to Medium
- **MVP Relevance:** Orbital enrichment and future tracking features

### 4.3 N2YO Satellite Tracking API

- **Organization:** N2YO (free API key)
- **Type:** API
- **Purpose:** Real-time satellite position and predicted passes for a ground location.
- **Sample Fields:** satid, satlat, satlng, satalt, azimuth, elevation, timestamp
- **Update Frequency:** Real-time
- **Historical Depth:** N/A (live)
- **Volume:** Small
- **MVP Relevance:** Live overpass context for dashboards (future)

---

## 5. Launch Data

### 5.1 Launch Library 2 (The Space Devs)

- **Organization:** The Space Devs
- **Type:** API (JSON)
- **Purpose:** Comprehensive launch schedules, providers, vehicles, and outcomes.
- **Sample Fields:** launch_id, name, net (launch_time), provider, vehicle, pad, status, mission_type
- **Update Frequency:** Continuous (event-driven)
- **Historical Depth:** Historical and upcoming launches
- **Volume:** Small
- **MVP Relevance:** Contextual reference only (launch analytics excluded from MVP)

### 5.2 SpaceX Public Data (r/SpaceX API)

- **Organization:** Community-maintained
- **Type:** API (JSON)
- **Purpose:** Historical SpaceX launches, payloads, and cores.
- **Sample Fields:** flight_number, mission_name, launch_date_utc, rocket, success, payloads
- **Update Frequency:** Event-driven (note: project in maintenance mode)
- **Historical Depth:** 2006-present
- **Volume:** Small
- **MVP Relevance:** Optional context only

---

## 6. Astronomical Data

### 6.1 NASA Open APIs (APOD, NeoWs)

- **Organization:** NASA
- **Type:** API (JSON)
- **Purpose:** Astronomy Picture of the Day and Near Earth Object tracking.
- **Sample Fields:** date, neo_reference_id, close_approach_date, miss_distance, estimated_diameter, is_hazardous
- **Update Frequency:** Daily
- **Historical Depth:** APOD 1995-present; NeoWs ongoing
- **Volume:** Small
- **MVP Relevance:** Future enrichment and engagement content

### 6.2 JPL Horizons

- **Organization:** NASA JPL
- **Type:** API + File
- **Purpose:** High-precision ephemerides for solar system bodies and spacecraft.
- **Sample Fields:** target, epoch, ra, dec, range, range_rate
- **Update Frequency:** On-demand computation
- **Historical Depth:** Long historical and future ephemerides
- **Volume:** Small
- **MVP Relevance:** Future expansion

### 6.3 Minor Planet Center

- **Organization:** IAU / Smithsonian
- **Type:** File + API
- **Purpose:** Orbital data for asteroids and comets.
- **Sample Fields:** designation, epoch, a, e, i, magnitude
- **Update Frequency:** Daily/weekly
- **Historical Depth:** Extensive
- **Volume:** Small to Medium
- **MVP Relevance:** Future expansion

---

## 7. Climate / Environmental Data

### 7.1 NOAA Climate Data Online (CDO)

- **Organization:** NOAA NCEI
- **Type:** API + Bulk
- **Purpose:** Historical weather and climate records (temperature, precipitation, wind).
- **Sample Fields:** station_id, date, tmax, tmin, prcp, wind_speed
- **Update Frequency:** Daily
- **Historical Depth:** Over a century for some stations
- **Volume:** Medium
- **MVP Relevance:** UC-15 fire weather context, UC-16 precipitation, UC-17 drought

### 7.2 Copernicus Climate Data Store (ERA5)

- **Organization:** ECMWF / Copernicus
- **Type:** API + Bulk
- **Purpose:** Global atmospheric reanalysis (temperature, humidity, wind, precipitation).
- **Sample Fields:** time, latitude, longitude, t2m, tp, u10, v10
- **Update Frequency:** Daily updates with ~5 day lag
- **Historical Depth:** 1940-present
- **Volume:** Large (subsettable to Medium)
- **MVP Relevance:** UC-15, UC-16, UC-17 — environmental drivers

### 7.3 NASA POWER

- **Organization:** NASA
- **Type:** API
- **Purpose:** Solar and meteorological data for any lat/lon, optimized for analytics.
- **Sample Fields:** date, latitude, longitude, T2M, PRECTOTCORR, ALLSKY_SFC_SW_DWN
- **Update Frequency:** Daily
- **Historical Depth:** 1981-present
- **Volume:** Small
- **MVP Relevance:** UC-15 fire risk, UC-17 drought — laptop-friendly point queries

### 7.4 Global Forest Watch

- **Organization:** World Resources Institute
- **Type:** API + Bulk
- **Purpose:** Forest cover, loss, and fire alerts.
- **Sample Fields:** alert_date, latitude, longitude, confidence, tree_cover_loss
- **Update Frequency:** Daily to weekly
- **Historical Depth:** 2001-present
- **Volume:** Medium
- **MVP Relevance:** UC-15 fire context, UC-14 land change

### 7.5 OpenAQ

- **Organization:** OpenAQ
- **Type:** API
- **Purpose:** Global air quality measurements, useful for wildfire smoke impact.
- **Sample Fields:** location, parameter, value, unit, datetime, coordinates
- **Update Frequency:** Near real-time
- **Historical Depth:** ~2015-present
- **Volume:** Small to Medium
- **MVP Relevance:** UC-15 wildfire smoke impact (secondary)

### 7.6 Copernicus Atmosphere Monitoring Service (CAMS)

- **Organization:** ECMWF / Copernicus
- **Type:** API + Bulk
- **Purpose:** Atmospheric composition including aerosols, fire emissions, and methane.
- **Sample Fields:** time, latitude, longitude, aod, co, ch4, pm2p5
- **Update Frequency:** Daily
- **Historical Depth:** ~2003-present
- **Volume:** Large (subsettable)
- **MVP Relevance:** UC-15 smoke/emissions, UC-28 methane (future)

---

## 8. Real-time Telemetry APIs

### 8.1 Global Fishing Watch API

- **Organization:** Global Fishing Watch
- **Type:** API (free key)
- **Purpose:** Apparent fishing effort and vessel activity derived from AIS, central to illegal fishing detection.
- **Sample Fields:** vessel_id, mmsi, lat, lon, timestamp, fishing_hours, flag, gear_type
- **Update Frequency:** Daily (some near real-time)
- **Historical Depth:** 2012-present
- **Volume:** Medium
- **MVP Relevance:** UC-18 illegal fishing — primary maritime feed

### 8.2 AIS Streams (AISHub / AISStream)

- **Organization:** AISHub / AISStream (community/free tiers)
- **Type:** Streaming + API
- **Purpose:** Live vessel positions and identity for maritime monitoring.
- **Sample Fields:** mmsi, latitude, longitude, sog, cog, heading, ship_type, timestamp
- **Update Frequency:** Real-time streaming
- **Historical Depth:** Limited (live focus)
- **Volume:** Medium (continuous stream)
- **MVP Relevance:** UC-18 illegal fishing, UC-19 vessel anomaly (future)

### 8.3 Open Notify ISS API

- **Organization:** Open Notify
- **Type:** API (JSON)
- **Purpose:** Real-time ISS position and crew, a simple live feed for streaming patterns.
- **Sample Fields:** timestamp, iss_position.latitude, iss_position.longitude, people
- **Update Frequency:** Real-time
- **Historical Depth:** N/A (live)
- **Volume:** Small
- **MVP Relevance:** Reference feed for validating streaming ingestion patterns

---

## Catalog Master Table

| # | Dataset | Category | Org | Type | Volume | MVP Relevance |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Sentinel-2 | Satellite | ESA | API/Bulk | Large | High |
| 2 | Sentinel-1 SAR | Satellite | ESA | API/Bulk | Large | High |
| 3 | Landsat 8/9 | Satellite | USGS/NASA | API/Bulk | Large | High |
| 4 | NASA GIBS/Worldview | Satellite | NASA | API | Small-Med | Medium |
| 5 | NASA FIRMS | EO | NASA | API/File | Small-Med | High |
| 6 | MODIS | EO | NASA | Bulk/API | Med-Large | High |
| 7 | VIIRS Fire | EO | NASA/NOAA | API/File | Small-Med | High |
| 8 | Copernicus EMS | EO | ESA | File | Medium | High |
| 9 | NASA Earthdata | EO | NASA | API/Bulk | Med-Large | High |
| 10 | Sentinel Hub Stats | EO | Sentinel Hub | API | Small | High |
| 11 | NOAA SWPC | Space Weather | NOAA | API | Small | Future |
| 12 | NASA DONKI | Space Weather | NASA | API | Small | Future |
| 13 | GOES X-ray | Space Weather | NOAA | API | Small | Future |
| 14 | CelesTrak | Orbital | CelesTrak | API/File | Small | Medium |
| 15 | Space-Track | Orbital | USSPACECOM | API | Small-Med | Medium |
| 16 | N2YO | Orbital | N2YO | API | Small | Future |
| 17 | Launch Library 2 | Launch | The Space Devs | API | Small | Low |
| 18 | SpaceX API | Launch | Community | API | Small | Low |
| 19 | NASA APOD/NeoWs | Astronomy | NASA | API | Small | Future |
| 20 | JPL Horizons | Astronomy | NASA JPL | API/File | Small | Future |
| 21 | Minor Planet Center | Astronomy | IAU | File/API | Small-Med | Future |
| 22 | NOAA CDO | Climate | NOAA | API/Bulk | Medium | High |
| 23 | ERA5 (CDS) | Climate | ECMWF | API/Bulk | Large | High |
| 24 | NASA POWER | Climate | NASA | API | Small | High |
| 25 | Global Forest Watch | Climate | WRI | API/Bulk | Medium | Medium |
| 26 | OpenAQ | Climate | OpenAQ | API | Small-Med | Medium |
| 27 | CAMS | Climate | ECMWF | API/Bulk | Large | Future |
| 28 | Global Fishing Watch | Telemetry | GFW | API | Medium | High |
| 29 | AIS Streams | Telemetry | AISHub | Stream/API | Medium | High |
| 30 | Open Notify ISS | Telemetry | Open Notify | API | Small | Low |

## Cross References

- Classification of these datasets is in [04-data-classification.md](./04-data-classification.md).
- Prioritization into tiers is in [06-data-prioritization.md](./06-data-prioritization.md).
- MVP subset is in [07-mvp-datasets.md](./07-mvp-datasets.md).
- Access endpoints are listed in [11-references.md](./11-references.md).
