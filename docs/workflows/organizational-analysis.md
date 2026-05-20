# Organizational Analysis Workflow

## Objective

Analyze existing repository structure and recommend improved organization while preserving trust, explainability, and reversibility.

Implementation entrypoint: `run_organizational_analysis()` in `kip_core.organization.recommendation_engine`.

---

## Step 1 — Folder Selection

User selects:

- repository root (`FolderSelection.root_folder_id`, `root_folder_name`)
- optional scope label

API: include `selection` in `POST /api/v1/organization/analyze`.

---

## Step 2 — Recursive Scan

Drive sync (future worker) or client supplies `ScannedDriveItem` list:

- folders and files
- `relative_path`, `mime_type`, `parent_folder_id`
- optional `raw_content` / `exported_text`

`analyzer.scan_items()` partitions folders vs documents.

---

## Step 3 — Content Extraction

`analyzer.extract_content()` per supported mime type. Profiles store `keywords` and `title_tokens` for clustering.

Extraction summary is returned on `OrganizationAnalysisResult.extraction_summary`.

---

## Step 4 — Semantic Analysis

- `clustering.cluster_documents()` — topic groups
- `structure_inference.assess_existing_structure()` — coherence score
- `analyzer.assess_scan_coverage()` — informational issues

---

## Step 5 — Organizational Inference

- `structure_inference.infer_proposed_folders()` — shallow semantic folders
- `rename_rules.propose_renames_for_profiles()` — filename normalization

---

## Step 6 — Recommendation Generation

`recommendation_engine.run_organizational_analysis()` emits `OrganizationRecommendation` objects.

Each recommendation includes:

| Field | Purpose |
|-------|---------|
| `recommendation_type` | `folder_create`, `file_move`, `file_rename`, `preserve_structure` |
| `rationale` | Short human-readable summary |
| `detailed_explanation` | Full explanation for review UI |
| `confidence_score` / `confidence_level` | Trust signal |
| `impacted_file_ids` | Scope of change |
| `proposed_destination_path` / `proposed_name` | Target state |
| `rollback` | `RollbackMetadata` for future reversal |

---

## Step 7 — Review Workflow

User may:

- approve recommendations
- reject recommendations
- selectively apply changes

*Not implemented in V1 engine — UI and execution layer are separate milestones.*

---

## Step 8 — Execution

Approved changes are executed safely and logged using rollback snapshots.

*Deferred — engine only prepares `RollbackMetadata` with `execution_deferred=True`.*

---

## Example API Request

```json
{
  "selection": {
    "root_folder_id": "folder-123",
    "root_folder_name": "Client Archive"
  },
  "items": [
    {
      "file_id": "file-1",
      "name": "invoice_2023_acme.pdf",
      "mime_type": "application/pdf",
      "relative_path": "invoice_2023_acme.pdf",
      "exported_text": "Invoice Acme 2023"
    }
  ],
  "preferences": {
    "prefer_minimal_changes": true,
    "enable_rename_recommendations": true
  }
}
```

---

## Success Criteria (MVP)

For a messy Drive folder inventory, Libby returns:

- proposed folder organization (`proposed_folders`, `file_move`, `folder_create`)
- proposed file renames (`file_rename`)
- confidence scores on every recommendation
- human-readable explanations (`rationale`, `detailed_explanation`)
- rollback preparation metadata on every recommendation
