# Known Issues — 2026-05-20

# Critical Architectural Issues

## Artifact Separation Is Incomplete

Current outputs are inconsistently distributed between:
- dataset folders
- repo artifact folders
- runtime summaries

This risks:
- benchmark contamination
- dataset pollution
- evaluation inconsistency

Desired separation:

/libby-datasets/
Raw benchmark datasets only

/libby-analysis/
Persistent evaluation artifacts

/tmp/libby/
Temporary runtime outputs

---

# Semantic Understanding Remains Weak

The engine still relies too heavily on:
- lexical overlap
- filename tokens
- shallow clustering signals

Symptoms:
- meaningless folder recommendations:
  - pdf/
  - img/
  - 1/
  - mzw/

The engine does not yet possess:
- organizational ontology
- workflow semantics
- canonical hierarchy understanding
- business-context awareness

---

# False Positive Detection Is Misleading

Current metric:
"Likely false positives: 0"

does NOT represent true semantic correctness.

It currently reflects:
- suppression heuristic success
- usefulness threshold filtering

Human review still identifies poor recommendations.

A true evaluation loop does not yet exist.

---

# Human Feedback Loop Missing

No system currently exists for:
- human scoring
- recommendation adjudication
- reinforcement signals
- semantic quality labeling

Needed eventually:
- recommendation review datasets
- approval/rejection capture
- usefulness feedback storage

---

# Evaluation Corpus Issues

Current benchmark datasets:
- are small
- inconsistent
- partially noisy
- not yet categorized by use case

No benchmark taxonomy exists yet.

No gold-standard organizational datasets exist yet.

---

# Extraction Coverage Remains Low

Current extraction coverage:
~22%

Many files still lack:
- extraction support
- OCR handling
- semantic enrichment

Especially:
- images
- HEIC
- embedded media
- proprietary formats

---

# "Copy Of" Rename Bug

Current rename normalization incorrectly transforms:

"Copy of X"

into:
"Of X"

instead of:
"X"

Known issue in rename_rules.py

---

# Semantic Cluster Naming Is Weak

Cluster labels remain shallow and noisy.

Examples:
- Mzw / Noqy / Iuj
- Pdf / Grade / Writing

Need:
- ontology-aware labels
- semantic summarization
- organizational-role naming

---

# BMAD Governance Is Underutilized

Implementation prompts have progressed faster than:
- governance docs
- ontology definitions
- workflow standards

Risk:
architectural entropy over time.

Future development must become more documentation-driven.

---

# No Organizational Ontology Exists Yet

The system lacks formal definitions for:
- good organization
- useful grouping
- canonical hierarchy
- organizational coherence
- structural preservation rules
- role-based access semantics

These concepts currently exist mostly implicitly.

This is becoming the primary conceptual bottleneck.

---

# No Ground Truth Evaluation Exists

The system currently lacks:
- gold-standard expected outputs
- curated benchmark datasets
- precision/recall metrics
- semantic quality scoring

Evaluation remains mostly heuristic + human intuition.

---

# Local Filesystem Only

Testing currently operates on:
- exported local Google Drive folders

No live Google Drive API integration exists yet.

No mutation-safe sandbox sync exists yet.

---

# Recommendation Granularity

The engine still emits:
- individual file moves

instead of:
- higher-level organizational plans

Future direction should likely shift toward:
- structural proposals
- organizational strategy recommendations
- grouped move plans

rather than isolated file-level actions.