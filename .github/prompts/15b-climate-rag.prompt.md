# Prompt 15b - RAG (Climate / Dust / Air-Quality Extension)

# Enterprise Space Mission Data & AI Platform

> **Phase 15b - Retrieval-Augmented Generation (Climate Expansion, Implementation)**

Read `.github/prompts/_shared.prompt.md` first. Extends Phase 15 (`rag/`). This is an **implementation** phase: build working, tested code plus docs.

---

# Objective

You are acting as Principal AI Architect and LLM/RAG Engineer.

Extend the existing RAG system to generate **grounded environmental reports and climate summaries** over the new climate/dust/air-quality Gold products, reusing the local LLM + Qdrant stack.

---

# Scope Guardrails

- Reuse the existing Ollama + sentence-transformers + Qdrant stack and pipelines. No new infra. Fit 16 GB RAM.
- Source only from certified 11b products and their docs; answers grounded with citations.
- No new source ingestion; no deferred (CAMS/ERA5/geostationary) content.

---

# Tasks

1. Source extension: add climate/dust/air-quality Gold summaries and dashboard narratives to the RAG corpus.
2. Chunking + metadata: tag chunks by AOI, date, pollutant/indicator for filtered retrieval.
3. Embeddings + index lifecycle: extend existing Qdrant collection; re-index strategy.
4. Retrieval: AOI/date/pollutant filters + hybrid search.
5. Generation templates:
   - Environmental / air-quality report generation
   - Dust-event summaries
   - Climate-indicator explanations (LST/NDVI/SST anomalies)
   - Satellite-image / index explanations (text grounded on metrics)
6. Guardrails: cite AOI + date + metric; no ungrounded numbers.
7. Evaluation: groundedness, relevance, latency on a climate eval set.
8. Freshness & re-indexing on new daily marts.
9. Tests: retrieval, grounding, regression eval for climate queries.
10. Trade-offs + ≥3 ADRs (metadata filters, report templating, freshness cadence).

---

# Deliverables

```
rag/ingest/climate/    (corpus builders)
rag/generate/          (extend: environmental report templates)
rag/eval/climate/      (eval set)
rag/tests/test_climate_rag.py
docs/rag/climate.md
```

# Acceptance Criteria

Index includes climate content, queries return cited grounded environmental answers, climate eval set passes thresholds.

# Definition of Done

A user can ask climate/dust/air-quality questions and get cited, grounded reports and summaries reproducibly. Stop here.
