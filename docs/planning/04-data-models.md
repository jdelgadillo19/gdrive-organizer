# Data Models

## Document
- id
- source_id
- title
- mime_type
- owner
- created_at
- updated_at
- checksum
- permission_hash

## DocumentChunk
- id
- document_id
- content
- embedding
- token_count
- chunk_index

## User
- id
- email
- role

## PermissionMapping
- id
- document_id
- principal
- permission_level

## SearchQueryLog
- id
- user_id
- query
- response_time
- retrieved_docs

## DocumentGovernance

- authority_level
- trust_score
- freshness_score
- reviewed_at
- reviewed_by
- lifecycle_status
- canonical_document_id

---

## DocumentRelationship

- id
- source_document_id
- target_document_id
- relationship_type
- confidence_score
- created_at

---

## DuplicateCluster

- id
- cluster_name
- canonical_document_id
- created_at

## Authority Levels

- canonical
- approved
- draft
- deprecated
- archived

## Lifecycle Status

- active
- under_review
- deprecated
- archived