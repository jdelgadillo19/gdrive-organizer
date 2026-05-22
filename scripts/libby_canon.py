#!/usr/bin/env python3
"""CLI for Libby canonization on local Drive export corpora."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages/kip_core/src"))

from kip_core.canon import format_canonization_markdown, run_canonization
from kip_core.canon.store import CanonArtifactStore, default_canon_analysis_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Libby canonization for local corpora")
    parser.add_argument(
        "corpus",
        type=Path,
        help="Path to corpus root or Desktop extract folder",
    )
    parser.add_argument(
        "--dataset",
        "-d",
        default="team-development",
        help="Dataset tag for saved artifacts",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Persist report under libby-analysis/",
    )
    parser.add_argument(
        "--analysis-root",
        type=Path,
        help="Override libby-analysis root",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout")
    parser.add_argument(
        "--canon-folder",
        default="Canon",
        help="Recommended relative path for canon documents",
    )
    args = parser.parse_args()

    try:
        result = run_canonization(
            args.corpus,
            canon_folder_relative=args.canon_folder,
        )
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    if args.save:
        store = CanonArtifactStore(
            root=args.analysis_root.resolve() if args.analysis_root else default_canon_analysis_root()
        )
        paths = store.save_run(result, dataset_name=args.dataset)
        print(f"Saved canon run: {paths.run_id}")
        print(f"  json: {paths.canon_json}")
        print(f"  md:   {paths.summary_md}")

    if args.json:
        print(json.dumps(result.model_dump(mode="json"), indent=2, default=str))
    else:
        print(format_canonization_markdown(result))

    gaps = [t for t in result.topics if t.gap]
    if gaps:
        print(f"\nWarning: {len(gaps)} canon topic(s) have no matching documents.", file=sys.stderr)
    if result.cross_reference_issues:
        high = sum(1 for i in result.cross_reference_issues if i.severity.value == "high")
        print(
            f"\nCross-reference issues: {len(result.cross_reference_issues)} "
            f"({high} high severity)",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
