# Document Governance

## Goal
Establish trust, authority, and lifecycle management for organizational knowledge.

---

# Authority Model

## Authority Levels

### Canonical
Official source of truth.

### Approved
Validated and usable.

### Draft
Work in progress.

### Deprecated
Superseded but retained historically.

### Archived
No longer operationally relevant.

---

# Document Lifecycle

1. Created
2. Reviewed
3. Approved
4. Published
5. Deprecated
6. Archived

---

# Governance Metadata

## Required Metadata

- owner
- department
- authority_level
- reviewed_at
- reviewed_by
- freshness_score
- trust_score

---

# Ownership Rules

Every document must have:
- accountable owner
- department assignment

Orphaned documents are flagged automatically.

---

# Review Policies

## Critical Policies
Review every 90 days.

## Operational SOPs
Review every 180 days.

## Informational Docs
Review annually.

---

# Canonicalization Workflow

When duplicate or conflicting docs are detected:

1. identify candidate canonical docs
2. notify owners
3. require human review
4. mark deprecated documents
5. establish relationships

---

# Governance Principles

- AI may recommend
- humans approve
- all governance actions are auditable