# Drive Sync Service

Worker that consumes `kip:queue:sync` messages and performs incremental Google Drive synchronization.

## Responsibilities

- Pull Drive changes using stored sync cursors
- Upsert document metadata and permission mappings
- Enqueue processing jobs on content change (idempotent keys)

## Status

Scaffold — implement in Milestone 1.
