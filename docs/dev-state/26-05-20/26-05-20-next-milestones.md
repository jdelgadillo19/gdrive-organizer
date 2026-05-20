# Next Milestones — 2026-05-20

# Immediate Priority

The next development phase should prioritize:
- semantic quality
- evaluation rigor
- ontology definition
- architectural discipline

NOT feature expansion.

---

# Milestone 1 — Artifact Architecture Cleanup

Goal:
Create a clean separation between:
- datasets
- runtime outputs
- persistent evaluation artifacts

Desired structure:

/libby-datasets/
/libby-analysis/
/tmp/libby/

Requirements:
- no artifact leakage into datasets
- append-only persistence
- reproducible runs
- stable dataset naming

---

# Milestone 2 — Organizational Ontology Foundation

Goal:
Define what "good organization" means.

Need formal documentation for:
- useful folder structures
- canonical hierarchy principles
- semantic grouping philosophy
- structural preservation rules
- organizational intent
- anti-patterns

This should become a first-class BMAD doc set.

---

# Milestone 3 — Human Evaluation Workflow

Goal:
Introduce human scoring and adjudication.

Needed:
- recommendation review schema
- approval/rejection tracking
- usefulness scoring
- semantic correctness labels
- reviewer notes

Long-term purpose:
build supervised evaluation datasets.

---

# Milestone 4 — Benchmark Corpus Development

Goal:
Create reusable benchmark datasets.

Need:
- curated messy datasets
- known-good organizational targets
- multiple organization styles:
  - educational
  - legal
  - finance
  - engineering
  - operations

Datasets should support:
- regression testing
- evaluation comparison
- benchmark scoring

---

# Milestone 5 — Semantic Quality Improvements

Goal:
Reduce shallow lexical clustering.

Need:
- ontology-aware clustering
- semantic summarization
- organizational-role reasoning
- better cluster labeling
- duplicate semantic suppression

The system must stop producing:
- img/
- pdf/
- mzw/
style outputs.

---

# Milestone 6 — Recommendation Strategy Upgrade

Goal:
Move from:
- isolated file moves

toward:
- organizational strategy recommendations

Examples:
- grouped move plans
- hierarchy refinement proposals
- structural reorganization plans
- naming policy recommendations

---

# Milestone 7 — Canonization System Design

Goal:
Begin defining canon governance.

Needed concepts:
- canon authority
- contradiction detection
- canonical replacement workflows
- semantic conflict analysis
- approval boundaries

This is a future core differentiator of Libby.

---

# Milestone 8 — Google Drive Integration Layer

Goal:
Safely connect to live Drive systems.

Requirements:
- read-only analysis mode first
- mutation sandboxing
- rollback capability
- approval-gated mutations
- scoped directory permissions

No automatic production mutations should occur.

---

# Milestone 9 — Governance & RBAC

Goal:
Prepare for multi-user future architecture.

Need:
- scoped permissions
- department boundaries
- admin review flows
- canon authority roles
- review queues

Still deferred for now, but must influence architecture decisions early.

---

# Milestone 10 — UI/UX Direction

Goal:
Eventually define:
- Drive widget UX
- review queue UX
- Ask Libby workflow
- submission workflow
- organization workflow

No UI implementation should begin until:
- ontology
- evaluation
- governance
- recommendation quality

are substantially more mature.

---

# Strategic Direction Reminder

Libby is NOT:
- a generic folder sorter
- a bulk rename utility
- a simple semantic search engine

Libby IS:
an organizational intelligence and canon-governance platform.

All future architectural decisions should reinforce this distinction.