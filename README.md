# GDrive Organizer — Knowledge Infrastructure Platform

# Libby (gdrive-organizer)

Libby is an AI-powered organizational intelligence and governance layer for existing knowledge repositories such as Google Drive.

Rather than replacing existing file systems, Libby integrates with them to provide:

- intelligent organization recommendations
- semantic file grouping
- filename normalization
- governance-aware retrieval
- canonization support
- contradiction detection
- explainable AI recommendations
- reversible organizational workflows

Libby is recommendation-first and human-in-the-loop by design. The system never performs destructive or organizational modifications without explicit user approval.

## Core Product Principles

- Human approval is required for all organizational modifications
- All file operations must be reversible
- AI recommendations must be explainable
- Existing high-quality organization should be preserved whenever possible
- Libby enhances existing repositories rather than replacing them
- Canonization and governance changes require elevated authorization
- Conservative recommendations are preferred over aggressive restructuring

## Architecture

- **Modular monolith** — FastAPI API + `kip_core` shared library
- **PostgreSQL + pgvector** — metadata, governance, embeddings
- **Redis** — job queues (sync, processing, embedding)
- **Governance-first retrieval** — ACL filter → eligibility → composite rank (never semantic-only)

See `docs/planning/` for full specifications.

## Primary Organizational Workflow

1. User selects a repository folder
2. Libby recursively analyzes contents
3. Documents are semantically classified
4. Existing structure quality is evaluated
5. Libby recommends:
   - folder restructuring
   - file relocation
   - filename normalization
6. User reviews recommendations
7. User approves or rejects changes
8. Approved operations are safely executed
9. Rollback snapshots are preserved

## Repository layout

```
apps/api/              FastAPI application
packages/kip_core/     Models, repositories, domain logic, organization engine, queues
services/              Worker scaffolds (drive-sync, embedding, …)
alembic/               Database migrations
infra/                 Dockerfiles
tests/                 Unit tests
```

## Prerequisites

- Python 3.12+
- Docker (for Postgres/pgvector and Redis)

## Quick start

```bash
cd gdrive-organizer
cp .env.example .env
# Edit .env — set JWT_SECRET; optionally Google OAuth credentials

python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

docker compose up -d postgres redis
alembic upgrade head

uvicorn kip_api.main:app --reload --app-dir apps/api/src --env-file .env
```

API docs: http://localhost:8000/api/docs

Set `PYTHONPATH` if needed:

```bash
export PYTHONPATH=packages/kip_core/src:apps/api/src
```

## Environment variables

See [.env.example](.env.example).

## API (v1)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/auth/google` | Start Google OAuth |
| GET | `/api/v1/auth/google/callback` | OAuth callback → JWT |
| GET | `/api/v1/auth/me` | Current user (Bearer) |
| POST | `/api/v1/search` | ACL-safe search |
| POST | `/api/v1/sync/start` | Enqueue sync job |
| GET | `/api/v1/sync/status` | Sync job status |
| GET | `/api/v1/documents/{id}` | Document + governance metadata |
| POST | `/api/v1/organization/analyze` | Organizational recommendations (no mutations) |

## Development

```bash
ruff check packages apps tests
pytest
```

## Critical design rules

1. **ACL before ranking** — enforced in `RetrievalService`
2. **Semantic similarity alone never determines order** — `rank_candidates()` uses composite weights from `23-ranking-and-scoring.md`
3. **AI is recommendation-only in V1** — no autonomous governance mutations
4. **Multi-tenant ready** — `tenant_id` on core tables

## Next milestones

Per `docs/planning/19-mvp-roadmap.md`:

1. Drive sync worker (incremental ingestion)
2. Document processing + embedding pipeline
3. Vector retrieval wired into `/search`
4. Citation-based search UI (Next.js)
