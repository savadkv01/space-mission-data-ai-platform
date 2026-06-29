# Prompt 15 - RAG

# Enterprise Space Mission Data & AI Platform

> **Phase 15 - Retrieval-Augmented Generation (Implementation)**

Read `.github/prompts/_shared.prompt.md` first. This is an **implementation** phase: build working, tested, containerized code plus docs.

---

# Objective

You are acting as Principal AI Architect and LLM/RAG Engineer.

Build a grounded RAG system over mission docs, telemetry summaries, weather bulletins, and Gold analytics, with a local LLM and vector store.

---

# Critical Rules

- Open-source only: local LLM (Ollama), embeddings (sentence-transformers), Qdrant vector DB (per architecture). Fit 16 GB RAM.
- Answers must be grounded with citations; no hallucinated facts.
- Provide tests, eval set, and one-command index + query.

---

# Tasks

1. RAG strategy: sources, consumers, grounding policy.
2. Document sources & ingestion from Gold/serving.
3. Chunking strategy + metadata.
4. Embeddings + vector store; index lifecycle.
5. Retrieval: hybrid search, filters, re-ranking.
6. Generation: prompt templates, citations, guardrails.
7. Evaluation: groundedness, relevance, latency.
8. Freshness & re-indexing.
9. Tests: retrieval, grounding, regression eval.
10. ≥10 incidents (stale index, low recall, hallucination, latency, embedding drift, etc.).
11. Trade-offs: Qdrant vs pgvector · chunk sizes · hybrid vs dense.
12. ≥5 ADRs.

---

# Deliverables

```
rag/ ingest/ embed/ retrieve/ generate/ eval/ tests/
docs/rag/ 01-strategy.md ... 12-adr.md 13-glossary.md README.md
```

# Acceptance Criteria

Index builds, queries return cited grounded answers, eval set passes thresholds, incidents documented.

# Definition of Done

A user can ask mission questions and get cited answers reproducibly. Stop here.
