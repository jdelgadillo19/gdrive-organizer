# Vector Search

## Retrieval Flow
1. Query embedding
2. Vector similarity search
3. Metadata filtering
4. Reranking
5. Citation assembly

## Search Constraints
- enforce ACL filtering before response generation
- prioritize freshness
- prioritize high-confidence documents

## Retrieval Quality Metrics
- recall
- precision
- citation relevance
- hallucination rate

## Search Enhancements
- hybrid BM25 + vector
- reranking models
- query expansion

## Retrieval Priorities

Ranking order:
1. ACL eligibility
2. authority level
3. freshness
4. semantic similarity
5. organizational relevance

---

## Duplicate Suppression

Prevent near-identical chunks from flooding results.

---

## Retrieval Transparency

Search responses should explain:
- why documents ranked highly
- authority level
- freshness status

## Governance-Aware Retrieval

Retrieval systems must prioritize:
1. ACL eligibility
2. authority level
3. freshness
4. semantic similarity

Deprecated or archived documents should rarely outrank canonical documents even when semantically similar.

Retrieval responses should expose:
- authority level
- review recency
- ownership metadata