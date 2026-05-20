# Cost Management

## Goal
Control operational AI and infrastructure costs.

---

# Major Cost Drivers

- embedding generation
- LLM inference
- re-indexing
- storage
- retrieval reranking

---

# Embedding Policies

## Only regenerate embeddings when:
- content changes materially
- chunking changes
- embedding model changes

---

# Caching

Cache:
- query embeddings
- retrieval results
- classification outputs

---

# Batch Processing

Prefer:
- asynchronous jobs
- batched embedding generation
- queue-driven ingestion

---

# Cost Monitoring

Track:
- embedding spend
- token usage
- retrieval frequency
- sync volume

---

# Rate Limiting

Protect:
- API providers
- ingestion systems
- user-facing latency

---

# Cost Principles

- optimize retrieval quality before model size
- avoid unnecessary re-embedding
- prioritize deterministic systems