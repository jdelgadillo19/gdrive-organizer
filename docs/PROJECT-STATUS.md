# Libby (gdrive-organizer) — project status

**Last updated:** 2026-05-22  
**Repo:** https://github.com/jdelgadillo19/gdrive-organizer  
**Latest commit (at update):** `44f72fd` — LaunchBuild1 canonization pipeline + party session doc

Use this file as the **session handoff** doc. Sprint decisions and party-mode detail: [`party-sessions/party-planning-session-2026-22-05.md`](./party-sessions/party-planning-session-2026-22-05.md). Historical org-first snapshot: [`dev-state/26-05-20/`](./dev-state/26-05-20/).

---

## Current state (what works)

| Area | Status |
|------|--------|
| **Sprint focus** | **Retrieval + canonization** (LaunchBuild1) — not folder-organization lead |
| **Organization engine** | `kip_core.organization` — scan, extract, cluster, recommend (no auto-mutations) |
| **Canonization** | `kip_core.canon` + `scripts/libby_canon.py` — topic assignment, cross-ref conflicts, canon recommendations |
| **Eval / org CLI** | `scripts/libby_eval.py` — artifacts under `libby-analysis/` (gitignored) |
| **Retrieval core** | `RetrievalService` — ACL → governance eligibility → composite rank; query embedding still placeholder |
| **API** | FastAPI: health, auth scaffolds, `POST /api/v1/search`, `POST /api/v1/organization/analyze` |
| **Tests** | 27 pytest tests passing |
| **Pilot corpus** | Team Development export on Desktop (see below) |

### Pilot corpus (Team Development)

| Item | Location |
|------|----------|
| Zip (source) | `~/Desktop/Team Development Resources-20260522T142219Z-3-001.zip` |
| Extracted tree (do not delete without explicit command) | `~/Desktop/Team Development Resources-20260522T142219Z-3-001/Team Development Resources/` |
| Latest canon run (local) | `libby-analysis/team-development/2026-05-22/canon-summary-20260522T144927Z.md` |

**Canonization run (2026-05-22):** 21 files, 100% extraction on pilot. Four LaunchBuild1 topics matched; 4 high-severity cross-reference issues flagged.

| Topic | Recommended canon (review before promoting) |
|-------|-----------------------------------------------|
| Role descriptions | `Leadership Roles.docx` |
| Master Sunday Service Plan | `Tech Team Guidelines/Sunday Tech Checklist.docx` *(may prefer Service Order Outline)* |
| Weekly Prep Plan | `SBB Platform Team Weekly Flow Timeline(1).docx` *(duplicate of non-(1) file)* |
| New Volunteer Onboarding | `New Volunteer Onboarding/Music Team/Audition Process.docx` |

**Not built yet:** `Canon/` folder on corpus, Ask with citations, golden eval harness, live Drive add-on, promote-to-canonical API, pgvector ingest pipeline.

---

## Known issues & limitations

| Item | Severity | Notes |
|------|----------|--------|
| **Cross-ref conflicts (pilot)** | High | 4 pairs need steward review (timeline dupes, service order vs weekly flow, roles vs leadership, worship tasks vs flow) — see latest canon summary |
| **Canon topic ranking** | Medium | Heuristic matcher may pick wrong “master” doc (e.g. tech checklist vs service order outline) |
| **No physical `Canon/` folder yet** | Expected | Recommendations only; no Drive moves or locked folder enforcement |
| **Ask / retrieval not wired to canon** | Blocking next milestone | `RetrievalService` ignores query text today (`_ = query`) |
| **No golden eval set** | High | G1–G2 gates from party session not implemented as `pytest`/CLI |
| **Rename bug** | Low | `rename_rules.py`: `"Copy of X"` → `"Of X"` |
| **Org engine shallow clustering** | Deferred | Lexical/pdf/img-style clusters; org is enricher only this sprint |
| **No UI / add-on** | Expected | GDrive popup (Ask \| Organize \| Upload) not started |
| **No live Drive** | Expected | Local export + Desktop zip only |
| **dev-state docs stale** | Doc | `docs/dev-state/26-05-20/` still org-first; trust **this file** + party session |

**Resolved recently**

- LaunchBuild1 canonization CLI and tests shipped (`44f72fd`).
- Party session captured retrieval pivot and canon rules.

---

## Next steps (agreed priority)

### Immediate (LaunchBuild1 — Week 2–3 spine)

1. **Steward review** — Resolve 4 cross-reference issues; pick one weekly flow timeline; confirm Master Sunday Service Plan canon (`Service Order Outline` vs `Sunday Tech Checklist`).
2. **Create `Canon/`** — Under pilot corpus root; copy or link promoted canon docs; read-wide, write restricted (Drive ACL + Libby promote workflow later).
3. **Re-run canonization** — `libby_canon.py` after promotions; confirm gaps closed.
4. **Golden eval set** — 15–25 questions + expected canon paths for team-development; automate G1/G2 metrics.
5. **Ask MVP** — Wire retrieval to corpus + canon metadata; cited answers or explicit gap (“recommend new doc”).

### Near-term

6. **Promote-to-canonical API/CLI** — Human approval record; audit trail (no auto-write to Drive).
7. **Upload path** — Compare upload vs formatting canon; flag conflicts for non-admin (approval ticket).
8. **Ingest + embeddings** — pgvector pipeline feeding `RetrievalService` semantic score.
9. **Align README / MVP roadmap** — State retrieval-first; org engine as enricher.

### Deferred

- Folder organization as lead feature  
- Live Drive OAuth (optional Week 4)  
- Full GDrive add-on shell  
- church-planning-buddy integration  

---

## Dev quick start

```bash
cd gdrive-organizer
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # JWT_SECRET, etc.

# Optional: Postgres + Redis for API
docker compose up -d postgres redis
alembic upgrade head

# Canonization on pilot corpus (read-only on Desktop tree)
python3 scripts/libby_canon.py \
  "$HOME/Desktop/Team Development Resources-20260522T142219Z-3-001" \
  --save --dataset team-development

# Org analysis (optional)
python3 scripts/libby_eval.py \
  "$HOME/Desktop/Team Development Resources-20260522T142219Z-3-001/Team Development Resources" \
  --save --dataset team-development

pytest
```

**Rules**

- Project root for edits: **`gdrive-organizer/`** unless told otherwise (e.g. reading Desktop corpus).
- Do **not** re-zip or delete the Desktop extract folder without an explicit command.

---

## Startup prompt (next session)

Copy into a new Cursor chat:

```
I'm continuing work on Libby (gdrive-organizer/).

Read docs/PROJECT-STATUS.md first for current state, known issues, and next steps.
For LaunchBuild1 product context, also skim docs/party-sessions/party-planning-session-2026-22-05.md.

Context:
- Sprint: retrieval + canonization (not org-first). Latest commit: 44f72fd.
- Canonization CLI works: scripts/libby_canon.py on Team Development corpus on Desktop.
- Pilot: ~/Desktop/Team Development Resources-20260522T142219Z-3-001/ (do not delete unzipped tree).
- Next: steward-review cross-refs, create Canon/ folder, wire Ask + golden eval.
- Independent of church-planning-buddy.

[Your task here — e.g. "Create Canon/ and promote recommended docs" or "Implement Ask CLI with citations"]
```

---

## Doc index

| File | Purpose |
|------|---------|
| [`PROJECT-STATUS.md`](./PROJECT-STATUS.md) | **This file** — progress & session handoff |
| [`party-sessions/party-planning-session-2026-22-05.md`](./party-sessions/party-planning-session-2026-22-05.md) | Party-mode decisions, sprint spine, canon rules |
| [`dev-state/26-05-20/26-05-20-current-state.md`](./dev-state/26-05-20/26-05-20-current-state.md) | Historical snapshot (org-first, May 20) |
| [`dev-state/26-05-20/26-05-20-known-issues.md`](./dev-state/26-05-20/26-05-20-known-issues.md) | Historical issues list |
| [`dev-state/26-05-20/26-05-20-next-milestones.md`](./dev-state/26-05-20/26-05-20-next-milestones.md) | Historical milestones (pre-pivot) |
| [`planning/21-retrieval-evaluation.md`](./planning/21-retrieval-evaluation.md) | Retrieval eval categories |
| [`planning/22-document-governance.md`](./planning/22-document-governance.md) | Authority levels & lifecycle |
| [`README.md`](../README.md) | Install & API overview |
