"""Persist canonization artifacts under libby-analysis/."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from kip_core.canon.models import CanonizationResult
from kip_core.canon.report import format_canonization_markdown
from kip_core.organization.evaluation.store import slugify_dataset_name


def default_canon_analysis_root() -> Path:
    env = os.environ.get("LIBBY_ANALYSIS_ROOT")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve() / "libby-analysis"


@dataclass(frozen=True)
class CanonArtifactPaths:
    run_id: str
    canon_json: Path
    summary_md: Path


class CanonArtifactStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or default_canon_analysis_root()).resolve()

    def save_run(self, result: CanonizationResult, *, dataset_name: str) -> CanonArtifactPaths:
        slug = slugify_dataset_name(dataset_name)
        stamp = result.analyzed_at.strftime("%Y-%m-%d")
        run_id = result.analyzed_at.strftime("%Y%m%dT%H%M%SZ")
        out_dir = self.root / slug / stamp
        out_dir.mkdir(parents=True, exist_ok=True)

        canon_json = out_dir / f"canon-{run_id}.json"
        summary_md = out_dir / f"canon-summary-{run_id}.md"

        payload = result.model_dump(mode="json")
        canon_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        summary_md.write_text(format_canonization_markdown(result), encoding="utf-8")

        index_path = self.root / slug / "canon-runs-index.json"
        index = []
        if index_path.exists():
            index = json.loads(index_path.read_text(encoding="utf-8"))
        index.append(
            {
                "run_id": run_id,
                "dataset": dataset_name,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
                "canon_json": str(canon_json),
                "summary_md": str(summary_md),
            }
        )
        index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

        return CanonArtifactPaths(run_id=run_id, canon_json=canon_json, summary_md=summary_md)
