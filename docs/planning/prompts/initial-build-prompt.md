# Initial Build Prompt

You are the lead engineer for the Knowledge Infrastructure Platform.

Your task is to scaffold the foundational backend architecture for a governance-aware enterprise knowledge retrieval platform.

The system is governance-aware, not just retrieval-aware.
Authority metadata is a first-class architectural concern.

Reference Documents:
- 00-project-overview.md
- 01-product-requirements.md
- 02-system-architecture.md
- 03-tech-stack.md
- 04-data-models.md
- 05-google-drive-sync.md
- 06-document-processing.md
- 07-vector-search.md
- 08-auth-and-permissions.md
- 09-api-specification.md
- 17-coding-standards.md
- 18-repository-structure.md
- 21-retrieval-evaluation.md
- 22-document-governance.md
- 23-ranking-and-scoring.md
- 24-knowledge-relationships.md
- 25-cost-management.md
- 26-governance-operating-model.md

Objectives:
1. Create the monorepo structure
2. Scaffold FastAPI backend
3. Configure PostgreSQL + pgvector
4. Implement Google OAuth foundation
5. Create governance-aware database models
6. Create migration setup
7. Implement incremental document sync pipeline
8. Add embedding job queue interfaces
9. Add ACL-safe semantic retrieval interfaces
10. Add ranking/scoring foundations
11. Add relationship modeling foundations
12. Add structured logging and configuration management

Requirements:
- typed Python
- modular architecture
- repository pattern
- dependency injection
- environment-based config
- Dockerized local development
- linting and formatting
- OpenAPI support
- test scaffolding
- deterministic pipelines first
- explainable retrieval behavior
- independently testable modules

Critical Constraints:
- retrieval must enforce ACL filtering BEFORE ranking
- semantic similarity alone must never determine ranking
- governance metadata must be first-class
- all AI systems must be recommendation-only
- avoid autonomous agents in V1
- preserve future multi-tenant compatibility
- all retrieval systems must follow governance operating model rules
- canonical documents must be prioritized over semantically similar lower-authority documents
- governance metadata must influence ranking behavior
- trust and explainability are first-class system concerns

Deliverables:
- complete folder structure
- dependency configuration
- Docker configuration
- SQLAlchemy models
- Alembic migrations
- service interfaces
- repository interfaces
- queue interfaces
- environment examples
- structured logging setup
- initial API routes
- README
- setup instructions

Implementation Strategy:
- output code incrementally by subsystem
- explain architectural decisions before implementation
- avoid over-engineering
- optimize for maintainability and operational trust