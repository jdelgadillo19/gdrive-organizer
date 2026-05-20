
# AI Bootstrap Context — GDrive Organizer

## Repository
- Repository Name: gdrive-organizer
- Primary Repo: https://github.com/jdelgadillo19/gdrive-organizer

---

# Project Identity

## Platform Name
Knowledge Infrastructure Platform

## Core Purpose
Build an AI-powered internal knowledge management and retrieval platform that synchronizes organizational knowledge from Google Drive, processes and indexes documents, and enables governance-aware semantic retrieval.

The system is explicitly designed to be:
- governance-aware
- ACL-safe
- citation-first
- authority-aware
- operationally trustworthy

---

# Primary System Goals

The platform must:

- Sync and index Google Drive content
- Preserve Google Drive permissions
- Support semantic search and RAG workflows
- Surface citations and retrieval transparency
- Detect stale or duplicate documentation
- Improve organizational knowledge quality over time

---

# Architectural Philosophy

## Guiding Principles

1. Deterministic pipelines first
2. AI augmentation second
3. Governance metadata is first-class
4. Retrieval must be explainable
5. ACL enforcement occurs BEFORE ranking
6. Humans approve all governance actions
7. Canonical documents outrank semantically similar low-authority content

---

# High-Level Architecture

## Core Components

### API Layer
- FastAPI backend
- REST endpoints
- JWT authentication
- OpenAPI-compatible schemas

### Sync Layer
- Google Drive incremental synchronization
- Webhook support
- Retry + dead-letter handling

### Processing Pipeline
- Text extraction
- Semantic chunking
- Metadata classification
- Embedding generation

### Retrieval Layer
- pgvector similarity search
- Hybrid retrieval support
- Governance-aware reranking
- Citation assembly

### Frontend
- Next.js application
- Search interface
- Chat retrieval UI
- Admin governance tooling

---

# Technology Stack

## Backend
- Python 3.12
- FastAPI
- SQLAlchemy
- Alembic

## Frontend
- Next.js
- React
- TailwindCSS
- shadcn/ui

## Database
- PostgreSQL
- pgvector

## Infrastructure
- Docker
- Redis
- Celery or Temporal

## Observability
- OpenTelemetry
- Prometheus
- Grafana

---

# Governance Model

## Authority Levels
- canonical
- approved
- draft
- deprecated
- archived

## Lifecycle States
- active
- under_review
- deprecated
- archived

## Governance Rules

- Semantic similarity alone must never determine ranking
- Deprecated documents should rarely outrank canonical documents
- AI systems may recommend actions only
- Humans must approve governance mutations
- Retrieval responses must expose authority and freshness metadata

---

# Retrieval Priorities

Ranking precedence:

1. ACL eligibility
2. Authority level
3. Freshness
4. Semantic similarity
5. Organizational relevance

---

# Security Requirements

- No permission bypass
- Least-privilege access
- Encrypted token storage
- Audit-safe operations
- Structured logging
- Role-based access control

---

# Repository Structure

/apps
  /api
  /web

/services
  /drive-sync
  /embedding
  /retrieval
  /maintenance

/packages
  /shared-types
  /prompt-library

---

# Engineering Standards

## Backend
- Typed Python
- Repository pattern
- Dependency injection
- Explicit interfaces
- Deterministic behavior

## Frontend
- Typed APIs
- Component isolation
- Minimal business logic in UI

---

# MVP Phases

## Phase 1 — Retrieval Foundation
- Google Drive ingestion
- Document processing
- ACL-safe vector retrieval
- Citation-first search UI

## Phase 2 — Governance Foundation
- Authority system
- Duplicate detection
- Stale document detection
- Governance workflows

## Phase 3 — Organizational Intelligence
- Relationship mapping
- Workflow clustering
- Knowledge insights
- Slack integrations

---

# Prompting Guidance For AI Agents

## When implementing backend services:
Reference:
- system architecture
- data models
- coding standards
- governance model
- ranking/scoring rules

## When implementing frontend features:
Reference:
- frontend UX
- governance visibility
- authority indicators
- retrieval transparency

## Critical Constraints
- Preserve ACL guarantees
- Preserve governance guarantees
- Maintain explainability
- Avoid hidden side effects
- Avoid autonomous mutation systems in V1

---

# Recommended AI Workflow

For implementation tasks:

1. Read bootstrap document first
2. Read relevant subsystem docs
3. Explain architecture before coding
4. Implement incrementally
5. Include tests
6. Preserve governance invariants

---

# Suggested Future AI Context Files

/docs/ai/
  bootstrap.md
  architecture-summary.md
  governance-model.md
  ranking-model.md
  retrieval-rules.md
  prompting-guide.md
  roadmap.md

---

# Current Project State

The project is currently in:
- architecture definition
- scaffold planning
- governance model definition
- retrieval system design

The current architecture target is a modular monolith with future microservice compatibility.

---

# Canonical Project Constraints

These constraints should be treated as non-negotiable:

- ACL filtering happens BEFORE retrieval ranking
- Governance metadata is first-class
- Retrieval must be explainable
- Citation visibility is mandatory
- AI recommendations require human approval
- Deterministic behavior is preferred over autonomous behavior
- Maintain future multi-tenant compatibility
