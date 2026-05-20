# Ranking and Scoring

## Goal
Ensure retrieval prioritizes trustworthy and operationally relevant knowledge.

## Retrieval Ranking Priorities

1. ACL eligibility
2. authority level
3. freshness
4. semantic relevance
5. organizational relevance

Semantic similarity alone must never determine final ranking.

---

# Ranking Pipeline

## Step 1 — ACL Filtering
Remove inaccessible documents before ranking.

---

## Step 2 — Authority Weighting

Priority:
1. canonical
2. approved
3. draft
4. deprecated
5. archived

Example weights:

- canonical = 1.0
- approved = 0.8
- draft = 0.5
- deprecated = 0.2
- archived = 0.1

---

## Step 3 — Freshness Weighting

Factors:
- review recency
- modification recency
- deprecation status

---

## Step 4 — Semantic Similarity

Vector similarity scoring.

---

## Step 5 — Organizational Relevance

Boost:
- user department
- frequently accessed docs
- project relevance

---

# Composite Score

Example:

final_score =
  semantic_score * 0.45 +
  authority_score * 0.25 +
  freshness_score * 0.15 +
  usage_score * 0.10 +
  metadata_quality_score * 0.05

---

# Result Transparency

Users should see:
- why documents ranked highly
- authority indicators
- freshness indicators

---

# Ranking Principles

- semantic similarity alone is insufficient
- stale docs should rarely outrank canonical docs
- explainability increases user trust