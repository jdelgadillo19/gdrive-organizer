# V1 Architecture

## Modular Monolith

| Layer | Location | Role |
|-------|----------|------|
| API | `apps/api/src/kip_api/` | HTTP routes, request/response schemas |
| Core services | `packages/kip_core/src/kip_core/services/` | Application service boundaries |
| Domain | `packages/kip_core/src/kip_core/domain/` | Pure governance and ranking logic |
| Organization engine | `packages/kip_core/src/kip_core/organization/` | Semantic analysis and recommendations |
| Persistence | `packages/kip_core/src/kip_core/db/` | SQLAlchemy models and sessions |
| Workers | `services/` | Async jobs (drive sync, embedding, …) |

## Organization Engine

The Organization Engine is responsible for semantic organizational analysis and recommendation generation. It does **not** execute file mutations.

```
packages/kip_core/src/kip_core/organization/
├── models.py                 # Recommendation schemas, rollback metadata
├── analyzer.py               # Scan inventory, extraction, profiling
├── clustering.py             # Lexical semantic clustering
├── structure_inference.py    # Coherence assessment, folder proposals
├── rename_rules.py           # Filename normalization
├── confidence_scoring.py     # Confidence levels and conservative caps
└── recommendation_engine.py  # Pipeline orchestration
```

### Pipeline

1. **Folder selection** — `FolderSelection` scopes analysis to a Drive root.
2. **Recursive scan** — caller supplies `ScannedDriveItem` inventory (Drive sync worker in future).
3. **Content extraction** — PDF (pypdf), DOCX/XLSX (stdlib XML), Google native via `exported_text`.
4. **Semantic clustering** — Jaccard similarity on keywords and title tokens.
5. **Structure inference** — coherence scoring; shallow folder proposals.
6. **Rename normalization** — conservative filename cleanup with collision avoidance.
7. **Recommendation generation** — typed recommendations with rationale and rollback metadata.
8. **Review / execution** — deferred; API returns recommendations only.

### Service Boundary

`OrganizationService` (`kip_core/services/organization.py`) is the integration point for API routes and future workers. Governance workflows can extend the same module without changing recommendation contracts.

### API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/organization/analyze` | Run analysis on scanned folder inventory |

## Retrieval (existing)

Governance-first retrieval remains in `RetrievalService` — ACL filter → eligibility → composite rank.

## Extension Points

- **Drive scan worker** — populate `ScannedDriveItem` from Google Drive API
- **Execution layer** — apply approved recommendations using `RollbackMetadata`
- **Governance** — post-MVP; hooks reserved via service boundaries, not in organization engine
