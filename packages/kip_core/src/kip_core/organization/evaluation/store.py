"""Persistent, append-only analysis artifact storage."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

from pydantic import TypeAdapter

from kip_core.organization.evaluation.comparison import compare_analysis_runs
from kip_core.organization.evaluation.metrics import build_run_metrics
from kip_core.organization.evaluation.models import (
    AnalysisRunArtifactPaths,
    RunComparisonReport,
    RunMetrics,
    RunRecord,
)
from kip_core.organization.evaluation.summary import render_summary_markdown
from kip_core.organization.models import (
    DocumentCluster,
    DocumentProfile,
    OrganizationAnalysisResult,
    OrganizationRecommendation,
)


def default_analysis_root() -> Path:
    """Resolve artifact root from LIBBY_ANALYSIS_ROOT or ./libby-analysis."""
    env = os.environ.get("LIBBY_ANALYSIS_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd() / "libby-analysis"


def slugify_dataset_name(name: str) -> str:
    """Convert a dataset label to a safe directory name."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "unnamed-dataset"


class AnalysisArtifactStore:
    """
    Append-only artifact store. Each run writes new timestamped files;
    previous runs are never overwritten.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or default_analysis_root()).resolve()

    def dataset_dir(self, dataset_slug: str) -> Path:
        return self.root / dataset_slug

    def _index_path(self, dataset_slug: str) -> Path:
        return self.dataset_dir(dataset_slug) / "runs-index.json"

    def list_runs(self, dataset_slug: str) -> list[RunRecord]:
        index_path = self._index_path(dataset_slug)
        if not index_path.exists():
            return []
        data = json.loads(index_path.read_text())
        return TypeAdapter(list[RunRecord]).validate_python(data)

    def get_latest_run(self, dataset_slug: str) -> RunRecord | None:
        runs = self.list_runs(dataset_slug)
        if not runs:
            return None
        return max(runs, key=lambda r: r.timestamp)

    def load_run_analysis(self, record: RunRecord) -> OrganizationAnalysisResult:
        return OrganizationAnalysisResult.model_validate_json(
            Path(record.paths["analysis_json"]).read_text()
        )

    def load_run_clusters(self, record: RunRecord) -> list[DocumentCluster]:
        data = json.loads(Path(record.paths["clusters_json"]).read_text())
        return TypeAdapter(list[DocumentCluster]).validate_python(data)

    def load_run_metrics(self, record: RunRecord) -> RunMetrics:
        return RunMetrics.model_validate_json(
            Path(record.paths["metrics_json"]).read_text()
        )

    def _artifact_paths(
        self,
        dataset_slug: str,
        run_id: str,
        timestamp: datetime,
    ) -> AnalysisRunArtifactPaths:
        date_partition = timestamp.strftime("%Y-%m-%d")
        artifact_stem = run_id
        run_dir = self.dataset_dir(dataset_slug) / date_partition
        run_dir.mkdir(parents=True, exist_ok=True)
        return AnalysisRunArtifactPaths(
            run_id=run_id,
            timestamp=timestamp,
            dataset_slug=dataset_slug,
            date_partition=date_partition,
            artifact_stem=artifact_stem,
            run_directory=str(run_dir),
            analysis_json=str(run_dir / f"analysis-{artifact_stem}.json"),
            clusters_json=str(run_dir / f"clusters-{artifact_stem}.json"),
            metrics_json=str(run_dir / f"metrics-{artifact_stem}.json"),
            summary_md=str(run_dir / f"summary-{artifact_stem}.md"),
        )

    def save_run(
        self,
        result: OrganizationAnalysisResult,
        *,
        dataset_name: str,
        profiles: list[DocumentProfile] | None = None,
        source_folder: str | None = None,
        similarity_threshold: float | None = None,
    ) -> AnalysisRunArtifactPaths:
        """
        Persist a complete analysis run (immutable files + index append).

        Never overwrites prior analysis-*.json / metrics-*.json files.
        """
        from kip_core.organization.evaluation.metrics import DEFAULT_SIMILARITY_THRESHOLD

        dataset_slug = slugify_dataset_name(dataset_name)
        prior_record = self.get_latest_run(dataset_slug)
        prior_metrics: RunMetrics | None = None
        prior_clusters: list[DocumentCluster] | None = None
        prior_recs: list[OrganizationRecommendation] | None = None

        if prior_record:
            prior_metrics = self.load_run_metrics(prior_record)
            prior_clusters = self.load_run_clusters(prior_record)
            prior_analysis = self.load_run_analysis(prior_record)
            prior_recs = prior_analysis.recommendations

        threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else DEFAULT_SIMILARITY_THRESHOLD
        )
        metrics = build_run_metrics(
            result,
            dataset_name=dataset_name,
            dataset_slug=dataset_slug,
            source_folder=source_folder,
            profiles=profiles,
            similarity_threshold=threshold,
            prior_metrics=prior_metrics,
            prior_clusters=prior_clusters,
            prior_recommendations=prior_recs,
        )

        paths = self._artifact_paths(dataset_slug, metrics.run_id, metrics.timestamp)

        comparison: RunComparisonReport | None = None
        if prior_record and prior_metrics and prior_clusters is not None and prior_recs:
            prior_result = self.load_run_analysis(prior_record)
            comparison = compare_analysis_runs(
                prior_result,
                result,
                baseline_metrics=prior_metrics,
                candidate_metrics=metrics,
            )

        analysis_payload = result.model_dump(mode="json")
        paths_dict = paths.model_dump()
        paths_dict.pop("run_directory", None)

        Path(paths.analysis_json).write_text(
            json.dumps(analysis_payload, indent=2, default=str),
            encoding="utf-8",
        )
        Path(paths.clusters_json).write_text(
            json.dumps(
                [c.model_dump(mode="json") for c in result.clusters],
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        Path(paths.metrics_json).write_text(
            metrics.model_dump_json(indent=2),
            encoding="utf-8",
        )
        Path(paths.summary_md).write_text(
            render_summary_markdown(
                result,
                metrics,
                profiles=profiles,
                comparison=comparison,
            ),
            encoding="utf-8",
        )

        record = RunRecord(
            run_id=metrics.run_id,
            timestamp=metrics.timestamp,
            date_partition=paths.date_partition,
            artifact_stem=paths.artifact_stem,
            paths={
                "analysis_json": paths.analysis_json,
                "clusters_json": paths.clusters_json,
                "metrics_json": paths.metrics_json,
                "summary_md": paths.summary_md,
            },
            metrics_snapshot={
                "document_count": metrics.document_count,
                "recommendation_count": metrics.recommendation_counts.total,
                "cluster_count": metrics.cluster_count,
                "coherence": metrics.structure_coherence_score,
                "false_positives": metrics.false_positives.likely_false_positive_count,
                "engine_hash": metrics.engine_version_hash,
            },
        )
        self._append_index(dataset_slug, record)
        return paths

    def _append_index(self, dataset_slug: str, record: RunRecord) -> None:
        self.dataset_dir(dataset_slug).mkdir(parents=True, exist_ok=True)
        index_path = self._index_path(dataset_slug)
        runs = self.list_runs(dataset_slug)
        runs.append(record)
        runs.sort(key=lambda r: r.timestamp)
        index_path.write_text(
            json.dumps(
                [r.model_dump(mode="json") for r in runs],
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    def compare_latest_two(self, dataset_slug: str) -> RunComparisonReport | None:
        """Compare the two most recent runs for a dataset."""
        runs = self.list_runs(dataset_slug)
        if len(runs) < 2:
            return None
        runs_sorted = sorted(runs, key=lambda r: r.timestamp)
        baseline_rec, candidate_rec = runs_sorted[-2], runs_sorted[-1]
        baseline = self.load_run_analysis(baseline_rec)
        candidate = self.load_run_analysis(candidate_rec)
        return compare_analysis_runs(
            baseline,
            candidate,
            baseline_metrics=self.load_run_metrics(baseline_rec),
            candidate_metrics=self.load_run_metrics(candidate_rec),
        )
