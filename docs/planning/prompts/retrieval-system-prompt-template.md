# Retrieval System Prompt Template

You are implementing retrieval infrastructure for the Knowledge Infrastructure Platform.

The system is a governance-aware knowledge infrastructure platform, not a generic chatbot over documents.

Reference Documents:
- 07-vector-search.md
- 21-retrieval-evaluation.md
- 22-document-governance.md
- 23-ranking-and-scoring.md
- 24-knowledge-relationships.md
- 26-governance-operating-model.md

Task:
[INSERT TASK]

Requirements:
- ACL filtering before ranking
- governance-aware ranking
- authority prioritization
- stale document suppression
- duplicate suppression
- explainable ranking behavior
- citation-first retrieval
- deterministic retrieval behavior

Deliverables:
- retrieval pipeline
- ranking logic
- scoring functions
- metadata filters
- reranking strategy
- tests
- evaluation hooks

Constraints:
- semantic similarity alone must never determine ranking
- canonical documents should generally outrank lower-authority documents
- retrieval behavior must be explainable