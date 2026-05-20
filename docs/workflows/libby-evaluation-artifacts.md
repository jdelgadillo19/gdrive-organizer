# Libby Evaluation Artifacts

Persistent, append-only analysis outputs for regression detection and heuristic tuning.

## Layout

```
libby-analysis/                    # LIBBY_ANALYSIS_ROOT or ./libby-analysis
  <dataset-slug>/
    runs-index.json                # append-only run catalog (never deletes prior runs)
    YYYY-MM-DD/
      analysis-<run-id>.json       # full OrganizationAnalysisResult
      clusters-<run-id>.json       # cluster snapshot
      metrics-<run-id>.json        # RunMetrics (evaluation metadata)
      summary-<run-id>.md          # human review summary
```

Dataset slugs are derived from tags such as `teacher-drive-export` or `messy-client-folder-v2`.

## CLI

```bash
# Analyze and persist (never overwrites prior runs)
python3 scripts/libby_eval.py /path/to/folder --save --dataset invoice-archive-test

# List runs for a dataset
python3 scripts/libby_eval.py --list-runs invoice-archive-test

# Compare latest two runs on a dataset
python3 scripts/libby_eval.py --compare invoice-archive-test

# Compare specific artifact files
python3 scripts/libby_eval.py --compare any \
  --baseline libby-analysis/.../analysis-<id>.json \
  --candidate libby-analysis/.../analysis-<id>.json
```

## Programmatic API

```python
from kip_core.organization import AnalysisArtifactStore, run_organizational_analysis

store = AnalysisArtifactStore()
result = run_organizational_analysis(selection, items)
paths = store.save_run(result, dataset_name="teacher-drive-export", profiles=profiles)
report = store.compare_latest_two("teacher-drive-export")
```

## Metrics persisted per run

- Engine version hash, timestamp, dataset identity
- Extraction statistics and coverage
- Recommendation counts and suppression estimates
- False-positive estimates, coherence, cluster cohesion
- Semantic configuration (threshold, embedder, preferences)
- Stability vs prior run (churn, repeat rate, cluster stability)
