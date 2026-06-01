# Party Planning Session — 2026-05-22

BMAD party-mode roundtable on **gdrive-organizer** (Libby). This document captures decisions, agent guidance, and sprint direction from the session. Use as the authoritative planning reference for **LaunchBuild1** until superseded.

**Session date:** 2026-05-22  
**Project root:** `/gdrive-organizer` (independent of church-planning-buddy unless explicitly directed otherwise)  
**Facilitator:** Cursor party mode (orchestrator + BMAD agents)

---

## Executive summary

Libby pivoted from **organization-first** (May 2026 dev-state) to **retrieval + canonization-first** for the next sprint. The immediate problem is management losing canonical business-practice documents in Drive, leading to duplicates, conflicts, and inaccessible SOPs/templates.

**LaunchBuild1** serves disorganized users (analyze, canonize, dedupe) and organized users (Ask with canon grounding, consistency checks, gap detection). UX: GDrive add-on with **Ask | Organize | Upload**; first run selects a database; thereafter Libby is idle until invoked; Drive remains usable manually.

**Canon model:** Dedicated read-accessible canon folder per database; writes require steward approval (harmonization / explicit intentional contradiction). Citations default to canon. Scope of canonization is **database-dependent**, not a fixed global count.

---

## Part 1 — Initial state analysis (party round 1)

### Current technical state (as of 2026-05-20 dev-state)

| Area | Status |
|------|--------|
| Stack | Python 3.12+, FastAPI modular monolith, `kip_core`, Postgres/pgvector + Redis planned |
| Organization engine | Shipped: analyzer, clustering, recommendations, evaluation artifacts |
| API | `POST /api/v1/organization/analyze`, search, auth scaffolds |
| Retrieval | `RetrievalService`: ACL → governance eligibility → composite rank; query embedding not fully wired |
| Tests | 24 pytest tests passing |
| Gaps | Shallow lexical clustering, ~22% extraction coverage, no human eval loop, no live Drive, no UI |
| Known bug | `rename_rules.py`: `"Copy of X"` → `"Of X"` |

### Strategic tension (resolved by Jesse)

- **Dev-state (May 20):** Org-intelligence eval platform; ontology + eval before feature expansion.
- **README/MVP roadmap:** Drive sync, embeddings, search UI.
- **Jesse override:** **Retrieval + canonization** is the next sprint focus. Analysis/ingest improves retrieval; org engine supports retrieval as async enricher, not sprint lead.

### Agent consensus (round 1, condensed)

- **Mary:** Trust and measurement before Drive/UI; align docs; benchmark + human eval.
- **John:** Built Phase 3 before Phase 1; ship ugly review + rigorous eval + one live folder; defer polished org UI.
- **Winston:** One inventory + ACL spine; org in shadow mode until eval passes; artifact hygiene blocking.
- **Amelia:** P0 rename fix + artifact dirs; then corpus, human review schema; defer sync/mutation/UI.

---

## Part 2 — Jesse’s answers and product direction

### UX and invocation (John Q1)

| State | Behavior |
|-------|----------|
| **First startup after install** | Initial sequence: user selects which **database** Libby organizes |
| **Subsequent startup** | Libby idle until invoked |
| **Invocation** | GDrive add-on button → popup with **Ask**, **Organize**, **Upload** |
| **Manual Drive use** | Unchanged; users can access documents normally without Libby |

### Pilot corpus (John Q2 — updated)

| Source | Path / notes |
|--------|----------------|
| ~~Personal Drive export~~ | Superseded for pilot |
| **Team development database** | `.zip` on Desktop: `/Users/SBBWD/Desktop/Team-development.....` (exact filename per machine) |
| Legacy reference | Personal Drive export at `~/Desktop/drive-download…` — no longer primary pilot |

### Project boundaries (John Q3)

- **church-planning-buddy:** Out of scope; completely independent project.
- **Edit root:** `/gdrive-organizer` unless directed otherwise (e.g. reading Desktop zip for ingest).

### LaunchBuild1 problem statement

Company management needs documents that codify business practices (onboarding, templates) but loses them in Drive. Staff recreate duplicates. Problems:

- No reliable find/access
- Multiple versions of the same document
- Conflicting versions

Different managers may oversee different databases with different styles. Libby must serve **both** disorganized and organized users.

| Persona | Capabilities |
|---------|----------------|
| **Disorganized** | Analyze what exists; resolve conflicts via canonization; consolidate near-duplicates into one authoritative document per purpose |
| **Organized** | Check inconsistencies across a managed database; **Ask** grounded in canon (“invoice format?”, “template for {situation}?”, “does this upload match formatting requirements?”); identify gaps where canon does not answer → recommend new doc |
| **Both** | Edge cases without canon coverage → Libby flags holes and recommends creating a policy doc |

---

## Part 3 — Sprint pivot: retrieval + canonization

### Sprint thesis (Winston)

> We make Ask trustworthy on a messy corpus by indexing, governing, and canonizing before we organize anyone’s folders.

### Reconciled 3-week spine (orchestrator)

| Week | Product focus | Engineering | Quality gates (Murat) |
|------|---------------|-------------|------------------------|
| **1 — Map the labyrinth** | Lock Team-development corpus; scope SOPs/templates | Ingest + chunk + embed; governance metadata; wire query into `RetrievalService` | G0 + golden set v0; baseline G1; target G2 |
| **2 — Pick the winner** | Canon workflow (human promote); dup/conflict report | Canon boost in rank; duplicate groups; promote API | G3 fixtures; canon in top-1 for golden queries |
| **3 — Ask before escalate** | Ask MVP (add-on or local shell); gap detection; citation UI | Ask + citations + “insufficient canon”; stub Organize/Upload | G4–G5 pilot checklist; LaunchBuild1 go/no-go |

**Defer this sprint:** folder org recommendations as lead feature, church-planning-buddy integration, full three-button parity (grey Organize/Upload until Ask passes citation gates), live Drive unless Week 3 is early green.

**Org engine role:** Post-ingest enricher (near-dup signals, quality scores) → rank features + offline eval only.

### Eval metric floors (Jesse: approved)

| Gate | Requirement |
|------|-------------|
| **G0** | Existing pytest + ACL-before-rank stay green |
| **G1** | ≥90% top-3 hit on 15–25 frozen Q→doc pairs from pilot |
| **G2** | 100% golden Ask answers have primary canon citation; 0 unsupported factual claims on golden set |
| **G3** | Near-dup pick; conflicts surfaced; gap → recommend new doc (no hallucinated policy) |
| **G4** | Upload review pass/fail vs formatting rules (representative set) |
| **G5** | Five manual walkthrough scenarios on pilot corpus |

**Daily habit:** Run golden metrics; if top-3 drops >5 points, fix retrieval before new features.

### Optional Week 4

Live Drive ingest for one database; add-on on real files; canonization remains human-in-the-loop.

---

## Part 4 — Canon designation and preservation

### Jesse clarification: how much to canonize

Canon scope is **per database**, not a fixed global number:

- Each database needs **at least one** canon document.
- Users may add **as many canon documents as needed**, provided **no two documents serve identical purposes**.

### Coexistence and cross-reference rules

| Case | Rule |
|------|------|
| **Unrelated purposes** | May coexist as canon (e.g. “invoice template” + “report template”) — little cross-reference needed |
| **Related same topic** | May coexist as **separate files** (e.g. “report template” + “report formatting guidelines”) — **high** cross-reference and reconciliation; Libby analyzes both, surfaces contradictions |
| **New upload vs existing canon** | If canon already exists for that purpose and new content contradicts: **flag**. Non-admin: cancel or send **approval ticket** to admin with options: reject submission; issue-by-issue accept/reject canon changes; or accept new doc as canon and deprecate old |

### Canon folder model (Jesse: accepted)

| Principle | Implementation |
|-----------|----------------|
| **Physical home** | Dedicated **canon root folder** per database in Drive |
| **Read access** | Broad read-only access |
| **Write access** | Steward approval + strict harmonization; intentional contradiction must be explicit |
| **Citations** | Ask and retrieval default to canon directory / `authority_level = canonical` |
| **Libby layer** | Promote workflow, metadata (`canonical_document_id`, relationships), ranking — folder ACL alone is insufficient |

**Note:** Folder identifies *where* truth lives; metadata identifies *which file* answers *which workflow* inside that folder.

---

## Part 5 — Pilot canon set (Team development database)

Minimum canon topics for LaunchBuild1 pilot sign-off:

1. **Role descriptions** — Leadership and Members; Music and Tech; Prep and Perform  
2. **Master Sunday Service Plan**  
3. **Weekly Prep Plan**  
4. **New Volunteer Onboarding**  

Each topic should resolve to **one canonical document per operational purpose** (or explicitly linked pair with reconciliation when two files serve related but distinct roles, per cross-reference rules above).

### Golden Ask examples (to label in eval set)

- Onboarding flow for new volunteers  
- What is the master plan for Sunday service?  
- Weekly prep expectations  
- Role expectations (by team: Leadership/Members, Music/Tech, Prep/Perform)  
- Report template vs formatting guidelines consistency (when both exist)

---

## Part 6 — Open items and follow-ups

| Item | Status |
|------|--------|
| Metric floors (G0–G5) | **Approved** by Jesse |
| Canon folder + promote workflow | **Accepted** by Jesse |
| Exact Team-development `.zip` filename on Desktop | **Done** — extract folder `Team Development Resources-20260522T142219Z-3-001` on Desktop |
| Canonization CLI | `scripts/libby_canon.py` — first run 2026-05-22 under `libby-analysis/team-development/` |
| `docs/product/launch-build-1-canon-folder.md` | Not yet written — optional next doc |
| Update `docs/dev-state` for retrieval sprint | Pending implementation phase |
| Align README/MVP roadmap with retrieval-first | Pending |

### Agent follow-ups (if continuing party mode)

- **Amelia:** Golden YAML, ingest script, `promote-canonical` API tasks  
- **Sally:** Add-on Ask shell UX  
- **John:** Sign-off golden question list once pilot files are inventoried  

---

## Part 7 — Agent transcripts (abbreviated)

Full subagent responses were delivered in chat. Key voices:

### 📋 John — 3-week LaunchBuild1 spine

- W1: corpus lock, ingest/profile, governance skeleton, retrieval eval v0  
- W2: conflict resolution, near-dup plan, rank v1 with canon boost, Ask dry-run  
- W3: Ask MVP, gap detection, citation UI, launch gate  
- Pushback: eval-first stays; hide Organize tab until Ask earns trust  

### 🏗️ Winston — 6-week technical spine (4-week cut available)

- Metadata envelope: identity, governance, ACL, org signals (async), retrieval  
- Hot path: store read only; no sync calls to org  
- Org: enricher → rank features → eval; no folder moves this sprint  

### 📊 Mary — success criteria

- Pilot exit: grounded citations + canonization without mandatory folder reorg  
- Phases 0–5 over ~2–3 weeks (calendar-flexible)  
- Measure recall@k, citation quality, dedupe, conflict detection, ACL safety  

### 🧪 Murat — quality gates

- G0→G5 sequencing; 15–25 golden questions; block on G0+G1 not eloquence  
- Citation gate before pretty conflict UI  

### 💻 Amelia — implementation slices (pre-pivot; still relevant for hygiene)

- P0: rename_rules copy-prefix fix  
- P0: `/libby-datasets/`, `/libby-analysis/`, `/tmp/libby/` layout  
- Defer mutation/sync/UI until eval gates pass  

---

## References

| Doc | Path |
|-----|------|
| Dev state | `docs/dev-state/26-05-20/` |
| Document governance | `docs/planning/22-document-governance.md` |
| Retrieval evaluation | `docs/planning/21-retrieval-evaluation.md` |
| Governance operating model | `docs/planning/26-governance-operating-model.md` |
| Ranking | `docs/planning/23-ranking-and-scoring.md` |
| Data models | `docs/planning/04-data-models.md` |
| MVP roadmap | `docs/planning/19-mvp-roadmap.md` |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | Initial session capture: party analysis, retrieval pivot, canon rules, Team-development pilot, approved eval floors |
