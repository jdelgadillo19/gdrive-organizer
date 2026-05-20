# Retrieval Evaluation Strategy

## Goal
Continuously measure retrieval quality, grounding accuracy, and citation correctness.

---

# Evaluation Categories

## 1. Retrieval Accuracy

Measure:
- correct document retrieval
- ranking quality
- recall@k
- precision@k

Questions:
- Was the correct document retrieved?
- Was it ranked appropriately?

---

## 2. Citation Quality

Measure:
- citation relevance
- citation completeness
- citation freshness

Questions:
- Did citations support the answer?
- Did citations reference authoritative sources?

---

## 3. Grounding Accuracy

Measure:
- hallucination rate
- unsupported claims
- synthesis correctness

Questions:
- Did the answer rely only on retrieved context?
- Did the answer invent policies or procedures?

---

## 4. Freshness Evaluation

Measure:
- stale document suppression
- prioritization of recently reviewed documents

Questions:
- Did deprecated docs outrank canonical docs?
- Were archived documents surfaced incorrectly?

---

## 5. ACL Enforcement Evaluation

Measure:
- unauthorized retrieval prevention

Questions:
- Could a user retrieve inaccessible content?
- Did permission filtering occur before ranking?

---

## 6. Conflict Detection Evaluation

Measure:
- contradictory document detection

Questions:
- Did the system identify conflicting SOPs?
- Were conflicts surfaced transparently?

---

# Gold Standard Dataset

Maintain:
- real company questions
- expected source documents
- expected citations
- expected answers

Dataset should evolve continuously.

---

# Evaluation Frequency

## Daily
- automated retrieval tests

## Weekly
- retrieval regression review

## Monthly
- human quality review

---

# Required Metrics

## Retrieval
- recall@5
- precision@5
- MRR

## LLM
- groundedness score
- hallucination rate

## Operational
- latency
- indexing failures
- sync failures

---

# Evaluation Principles

- evaluation is mandatory before production rollout
- retrieval quality matters more than model sophistication
- citations are first-class outputs