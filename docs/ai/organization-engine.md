# Organization Engine

## Purpose

The Organization Engine generates organizational recommendations for repository contents. It is recommendation-first: no automatic file modification.

Implementation: `packages/kip_core/src/kip_core/organization/`

---

## Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `models.py` | Pydantic schemas: recommendations, rollback metadata, scan items |
| `analyzer.py` | Extraction, profiling, scan partitioning |
| `clustering.py` | Hybrid semantic grouping (embeddings + lexical + context) |
| `embeddings.py` | Corpus TF-IDF vectors; optional sentence-transformers |
| `semantic_features.py` | Operational role, temporal/path context signals |
| `recommendation_filtering.py` | Usefulness thresholds, anti-overorganization |
| `explanations.py` | Rich rationale and detailed explanations |
| `eval_tools.py` | Cluster inspection and false-positive analysis |
| `evaluation/` | Persistent artifacts, run metrics, comparison, summaries |
| `structure_inference.py` | Coherence assessment, proposed folders |
| `rename_rules.py` | Filename normalization proposals |
| `confidence_scoring.py` | Scores and conservative caps |
| `recommendation_engine.py` | End-to-end `run_organizational_analysis()` |

---

## Responsibilities

- semantic clustering
- taxonomy / folder structure inference
- filename normalization
- folder structure recommendation
- confidence scoring
- rationale generation
- rollback-preparation metadata on every recommendation

---

## Organizational Heuristics

### Preserve Existing Quality

`assess_existing_structure()` scores folder coherence. When `is_well_organized` is true, the engine emits a `preserve_structure` recommendation and caps relocation confidence.

### Avoid Excessive Nesting

`AnalysisPreferences.max_proposed_depth` limits proposed folder depth (default 3).

### Semantic Grouping

`cluster_documents()` combines TF-IDF embedding similarity (default), optional
`sentence-transformers` when installed, lexical overlap, folder/temporal context,
and operational-role alignment. Clusters expose `similarity_breakdown` and
`relationship_type` for explainability.

### Conservative Recommendations

`apply_conservative_cap()` lowers scores when existing structure is coherent and `prefer_minimal_changes` is enabled. Low-confidence relocations may be omitted entirely.

---

## Rename Heuristics

Normalize:

- dates → `YYYY-MM-DD`
- separators and casing
- version/copy noise (`final`, `v1`, `(copy)`)

Preserve:

- file extensions
- document identity (no overwrite semantics)

Avoid:

- filename collisions in the same analysis batch

---

## Confidence Scoring

| Level | Score | Behavior |
|-------|-------|----------|
| High | ≥ 0.75 | Strong cluster cohesion and extraction coverage |
| Medium | ≥ 0.50 | Review before approval |
| Low | < 0.50 | Informational; relocations may be skipped when conservative |

---

## Anti-Chaos Rules

- Never delete automatically
- Never overwrite files automatically
- Never aggressively restructure low-confidence groups
- Preserve rollback metadata for all recommendations
- Explain every recommendation (`rationale` + `detailed_explanation`)
- `requires_approval=True`, `auto_apply_allowed=False` on all V1 recommendations

---

## Content Extraction

| Type | Strategy |
|------|----------|
| PDF | `pypdf` when `raw_content` provided |
| DOCX | stdlib ZIP + `word/document.xml` |
| XLSX | stdlib ZIP + `xl/sharedStrings.xml` |
| Google Docs / Sheets | `exported_text` from Drive export (sync worker) |
| PPTX | stdlib ZIP + slide XML (`a:t` text nodes) |
| Scanned PDF | `pypdf` then optional OCR (`pytesseract` + `pdf2image`) |
| Plain text | UTF-8 decode of `raw_content` |

Extractions include `confidence` and `provenance` for trust signals.

---

## Usage

```python
from kip_core.organization import (
    FolderSelection,
    ScannedDriveItem,
    run_organizational_analysis,
)

result = run_organizational_analysis(
    FolderSelection(root_folder_id="abc", root_folder_name="Client Files"),
    scanned_items,
)
for rec in result.recommendations:
    print(rec.title, rec.confidence_level, rec.rationale)
```
