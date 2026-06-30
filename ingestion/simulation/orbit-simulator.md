# Orbit Simulator

Code: [orbit_simulator.py](orbit_simulator.py). Narrative: [docs/ingestion/06-simulation.md](../../docs/ingestion/06-simulation.md).

- Propagates real TLEs with **SGP4** (`sgp4` package) → ECI → geodetic (lat/lon/alt).
- **Analytic circular-LEO fallback** when `sgp4` is unavailable, so demos/tests run offline.
- Seed TLEs included (ISS + samples); replaceable at runtime from the CelesTrak connector.
- Emits `orbit_position` schema; records tagged with `propagator` (`sgp4`/`analytic`).
