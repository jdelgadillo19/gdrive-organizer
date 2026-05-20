#!/usr/bin/env python3
"""CLI for Libby organizational analysis, artifact persistence, and regression comparison."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages/kip_core/src"))

from kip_core.organization.analyzer import build_document_profiles, scan_items
from kip_core.organization.clustering import pairwise_similarity_debug
from kip_core.organization.embeddings import fit_corpus_embeddings
from kip_core.organization.eval_tools import (
    evaluate_recommendation_usefulness,
    format_cluster_report,
    inspect_clusters,
)
from kip_core.organization.evaluation.comparison import (
    compare_runs_from_artifacts,
    format_comparison_markdown,
)
from kip_core.organization.evaluation.store import (
    AnalysisArtifactStore,
    default_analysis_root,
    slugify_dataset_name,
)
from kip_core.organization.models import DriveMimeType, FolderSelection, ScannedDriveItem
from kip_core.organization.recommendation_engine import run_organizational_analysis

_MIME_BY_SUFFIX = {
    ".pdf": DriveMimeType.PDF,
    ".docx": DriveMimeType.DOCX,
    ".xlsx": DriveMimeType.XLSX,
    ".pptx": DriveMimeType.PPTX,
    ".txt": DriveMimeType.PLAIN_TEXT,
}


def _scan_local_folder(root: Path) -> list[ScannedDriveItem]:
    items: list[ScannedDriveItem] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root))
        suffix = path.suffix.lower()
        mime = _MIME_BY_SUFFIX.get(suffix, "application/octet-stream")
        raw = path.read_bytes() if suffix in _MIME_BY_SUFFIX else None
        items.append(
            ScannedDriveItem(
                file_id=rel,
                name=path.name,
                mime_type=mime,
                relative_path=rel,
                raw_content=raw,
            )
        )
    return items


def _cmd_list_runs(store: AnalysisArtifactStore, dataset: str) -> int:
    slug = slugify_dataset_name(dataset)
    runs = store.list_runs(slug)
    if not runs:
        print(f"No runs for dataset '{dataset}' ({slug})")
        return 0
    for rec in runs:
        snap = rec.metrics_snapshot
        print(
            f"{rec.timestamp.isoformat()}  {rec.run_id}  "
            f"recs={snap.get('recommendation_count')}  "
            f"clusters={snap.get('cluster_count')}  "
            f"fp={snap.get('false_positives')}"
        )
    return 0


def _cmd_compare(
    store: AnalysisArtifactStore,
    dataset: str,
    *,
    baseline_path: Path | None,
    candidate_path: Path | None,
) -> int:
    slug = slugify_dataset_name(dataset)
    if baseline_path and candidate_path:
        report = compare_runs_from_artifacts(baseline_path, candidate_path)
        print(format_comparison_markdown(report))
        return 0
    report = store.compare_latest_two(slug)
    if report is None:
        print("Need at least two runs to compare.", file=sys.stderr)
        return 1
    print(format_comparison_markdown(report))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Libby organizational analysis, artifacts, and regression comparison"
    )
    parser.add_argument("folder", type=Path, nargs="?", help="Local folder to analyze")
    parser.add_argument(
        "--dataset",
        "-d",
        help="Dataset name/tag for evaluation (e.g. teacher-drive-export)",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Persist append-only artifacts under libby-analysis/",
    )
    parser.add_argument(
        "--analysis-root",
        type=Path,
        help="Override artifact root (default: ./libby-analysis or LIBBY_ANALYSIS_ROOT)",
    )
    parser.add_argument("--list-runs", metavar="DATASET", help="List saved runs for a dataset")
    parser.add_argument(
        "--compare",
        metavar="DATASET",
        help="Compare two runs (latest pair, or use --baseline/--candidate paths)",
    )
    parser.add_argument("--baseline", type=Path, help="Baseline analysis-*.json path")
    parser.add_argument("--candidate", type=Path, help="Candidate analysis-*.json path")
    parser.add_argument(
        "--clusters-only",
        action="store_true",
        help="Print cluster inspection only",
    )
    parser.add_argument(
        "--pair",
        nargs=2,
        metavar=("FILE_A", "FILE_B"),
        help="Debug semantic similarity between two relative paths",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    root_override = args.analysis_root
    store = AnalysisArtifactStore(
        root=root_override.resolve() if root_override else default_analysis_root()
    )

    if args.list_runs:
        return _cmd_list_runs(store, args.list_runs)

    if args.compare:
        return _cmd_compare(
            store,
            args.compare,
            baseline_path=args.baseline,
            candidate_path=args.candidate,
        )

    if not args.folder:
        parser.error("folder is required unless using --list-runs or --compare")
        return 1

    root = args.folder.resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 1

    dataset_name = args.dataset or root.name
    selection = FolderSelection(root_folder_id=str(root), root_folder_name=root.name)
    items = _scan_local_folder(root)

    if args.pair:
        _folders, documents = scan_items(items)
        profiles = build_document_profiles(documents, selection=selection)
        id_a = next((p.file_id for p in profiles if p.file_id.endswith(args.pair[0])), args.pair[0])
        id_b = next((p.file_id for p in profiles if p.file_id.endswith(args.pair[1])), args.pair[1])
        model = fit_corpus_embeddings(profiles)
        pa = next(p for p in profiles if p.file_id == id_a)
        pb = next(p for p in profiles if p.file_id == id_b)
        report = pairwise_similarity_debug(pa, pb, model=model)
        print(json.dumps(report, indent=2) if args.json else report)
        return 0

    result = run_organizational_analysis(selection, items)
    _folders, documents = scan_items(items)
    profiles = build_document_profiles(documents, selection=selection)

    if args.save:
        paths = store.save_run(
            result,
            dataset_name=dataset_name,
            profiles=profiles,
            source_folder=str(root),
        )
        print(f"Saved run: {paths.run_id}")
        print(f"  analysis: {paths.analysis_json}")
        print(f"  summary:  {paths.summary_md}")
        print(f"  metrics:  {paths.metrics_json}")
        return 0

    if args.clusters_only:
        output = [c.model_dump() for c in inspect_clusters(result.clusters)]
        print(json.dumps(output, indent=2) if args.json else format_cluster_report(result.clusters))
        return 0

    usefulness = evaluate_recommendation_usefulness(result, profiles=profiles)
    if args.json:
        print(
            json.dumps(
                {
                    "clusters": [c.model_dump() for c in result.clusters],
                    "recommendations": [r.model_dump(mode="json") for r in result.recommendations],
                    "usefulness": [u.__dict__ for u in usefulness],
                },
                indent=2,
                default=str,
            )
        )
    else:
        print(format_cluster_report(result.clusters))
        print()
        print(f"Recommendations: {len(result.recommendations)}")
        for rec in result.recommendations[:15]:
            print(f"  [{rec.confidence_level.value}] {rec.title}")
        flagged = [u for u in usefulness if u.likely_false_positive]
        if flagged:
            print(f"\nLikely false positives ({len(flagged)}):")
            for row in flagged[:10]:
                print(f"  - {row.title} (usefulness={row.usefulness_estimate})")
        print(f"\nTip: use --save --dataset '{dataset_name}' to persist under {store.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
