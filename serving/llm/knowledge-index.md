# Knowledge Index (Task 8)

Definition of the Qdrant collection(s) that back the RAG assistant. The index is
built by the embedding pipeline (AI/ML subsystem) from serveable, Gold-derived
content only.

## Collections

| Collection | Content | Chunk unit | Refresh |
| --- | --- | --- | --- |
| `kb_products` | daily data-product summaries | 1 AOI/day or vessel/day narrative | after serving refresh |
| `kb_catalog` | imagery catalog metadata | 1 scene | daily |
| `kb_docs` | architecture + design docs | heading section | on doc change |
| `kb_incidents` | incident reports + runbooks | 1 incident | on new incident |

## Chunk Schema

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | uuid | chunk identity |
| `vector` | float[] | embedding |
| `text` | string | chunk content |
| `source` | string | serving product / doc path |
| `use_case` | string | UC-15 … UC-27 (nullable for docs) |
| `entity_key` | string | aoi_key / scene_key / vessel_key |
| `date_key` | string | event date (nullable) |
| `classification` | enum | public / internal / sensitive |
| `track` | enum | mvp / sim |
| `citation` | string | human-readable source reference |

## Index Settings (conceptual)

| Setting | Value | Rationale |
| --- | --- | --- |
| Distance | cosine | normalized text embeddings |
| Embedding model | local sentence-transformer via Ollama | open-source, laptop-viable |
| Dimensions | model-defined (e.g. 384/768) | match embedding model |
| Payload filters | `classification`, `track`, `use_case`, `aoi_key` | scoped + governed retrieval |
| Top-k | 5 (tunable) | grounding without prompt bloat |

## Governance Hooks

- **Classification filter** enforced at query time — sensitive chunks require an
  authorized scope (mirrors [../access-strategy.md](../access-strategy.md)).
- **Track filter** — `sim` chunks excluded from production analyst answers.
- **Freshness** — `kb_products` chunks are versioned by `date_key`; stale chunks
  are replaced, not appended, after each serving refresh.
- **Traceability** — every returned chunk carries a `citation` back to a serving
  product or doc, preserving the platform lineage guarantee end-to-end.
