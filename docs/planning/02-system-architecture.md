# System Architecture

## High-Level Components

### API Layer
- FastAPI backend
- REST endpoints
- Auth middleware

### Sync Service
- Google Drive integration
- Incremental updates
- Queue dispatching

### Processing Pipeline
- Text extraction
- Chunking
- Metadata extraction
- Embedding generation

### Retrieval Engine
- Vector similarity search
- Metadata filtering
- Reranking

### Frontend
- Next.js dashboard
- Search interface
- Admin tools

## Architecture Style
Modular monolith initially.
Can evolve into microservices later.

## Key Design Principles
- Deterministic pipelines first
- AI augmentation second
- Permission-safe retrieval
- Strong metadata ownership