"""Compare two persisted or in-memory analysis runs for regression detection."""

from __future__ import annotations

from pathlib import Path

from kip_core.organization.evaluation.fingerprints import recommendation_fingerprint
from kip_core.organization.evaluation.metrics import RunMetrics
from kip_core.organization.evaluation.models import RunComparisonReport
from kip_core.organization.evaluation.stability import (
    cluster_stability_score,
    recommendation_churn,
    semantic_drift_inspection,
)
from kip_core.organization.models import OrganizationAnalysisResult


def compare_analysis_runs(
    baseline: OrganizationAnalysisResult,
    candidate: OrganizationAnalysisResult,
    *,
    baseline_metrics: RunMetrics,
    candidate_metrics: RunMetrics,
) -> RunComparisonReport:
    """Produce a delta report between baseline (older) and candidate (newer) runs."""
    rec_delta = (
        candidate_metrics.recommendation_counts.total
        - baseline_metrics.recommendation_counts.total
    )
    by_type_delta: dict[str, int] = {}
    all_types = set(baseline_metrics.recommendation_counts.by_type) | set(
        candidate_metrics.recommendation_counts.by_type
    )
    for key in all_types:
        by_type_delta[key] = candidate_metrics.recommendation_counts.by_type.get(
            key, 0
        ) - baseline_metrics.recommendation_counts.by_type.get(key, 0)

    churn, repeat, added, removed = recommendation_churn(
        baseline.recommendations, candidate.recommendations
    )
    cluster_stability = cluster_stability_score(baseline.clusters, candidate.clusters)
    drift = semantic_drift_inspection(baseline.clusters, candidate.clusters)

    coherence_delta = round(
        candidate_metrics.structure_coherence_score
        - baseline_metrics.structure_coherence_score,
        4,
    )
    extraction_delta = round(
        candidate_metrics.extraction.coverage_ratio
        - baseline_metrics.extraction.coverage_ratio,
        4,
    )
    fp_delta = (
        candidate_metrics.false_positives.likely_false_positive_count
        - baseline_metrics.false_positives.likely_false_positive_count
    )

    notable: list[str] = []
    if rec_delta < 0:
        notable.append(f"Recommendation count decreased by {abs(rec_delta)}.")
    elif rec_delta > 0:
        notable.append(f"Recommendation count increased by {rec_delta}.")
    if fp_delta < 0:
        notable.append(f"Likely false positives reduced by {abs(fp_delta)}.")
    elif fp_delta > 0:
        notable.append(f"Likely false positives increased by {fp_delta}.")
    if extraction_delta > 0.05:
        notable.append(f"Extraction coverage improved (+{extraction_delta:.2f}).")
    if cluster_stability < 0.5:
        notable.append(f"Low cluster stability ({cluster_stability:.2f}) — semantic drift likely.")
    if churn > 0.6:
        notable.append(f"High recommendation churn ({churn:.2f}).")

    added_titles = [
        next(
            (r.title for r in candidate.recommendations if recommendation_fingerprint(r) == fp),
            fp,
        )
        for fp in sorted(added)[:15]
    ]
    removed_titles = [
        next(
            (r.title for r in baseline.recommendations if recommendation_fingerprint(r) == fp),
            fp,
        )
        for fp in sorted(removed)[:15]
    ]

    return RunComparisonReport(
        baseline_run_id=baseline_metrics.run_id,
        candidate_run_id=candidate_metrics.run_id,
        baseline_timestamp=baseline_metrics.timestamp,
        candidate_timestamp=candidate_metrics.timestamp,
        dataset_baseline=baseline_metrics.dataset_name,
        dataset_candidate=candidate_metrics.dataset_name,
        recommendation_count_delta=rec_delta,
        recommendation_count_delta_by_type=by_type_delta,
        cluster_count_delta=candidate_metrics.cluster_count - baseline_metrics.cluster_count,
        coherence_delta=coherence_delta,
        extraction_coverage_delta=extraction_delta,
        false_positive_delta=fp_delta,
        cluster_stability_score=cluster_stability,
        recommendation_churn_rate=churn,
        repeat_recommendation_rate=repeat,
        semantic_drift=drift,
        new_recommendations=added_titles,
        removed_recommendations=removed_titles,
        notable_changes=notable,
    )


def compare_runs_from_artifacts(
    baseline_analysis_path: Path,
    candidate_analysis_path: Path,
) -> RunComparisonReport:
    """Load two saved analysis artifacts and compare them."""
    baseline_dir = baseline_analysis_path.parent
    candidate_dir = candidate_analysis_path.parent
    baseline_stem = baseline_analysis_path.stem.replace("analysis-", "")
    candidate_stem = candidate_analysis_path.stem.replace("analysis-", "")

    baseline_metrics = RunMetrics.model_validate_json(
        (baseline_dir / f"metrics-{baseline_stem}.json").read_text()
    )
    candidate_metrics = RunMetrics.model_validate_json(
        (candidate_dir / f"metrics-{candidate_stem}.json").read_text()
    )
    baseline = OrganizationAnalysisResult.model_validate_json(
        baseline_analysis_path.read_text()
    )
    candidate = OrganizationAnalysisResult.model_validate_json(
        candidate_analysis_path.read_text()
    )
    return compare_analysis_runs(
        baseline,
        candidate,
        baseline_metrics=baseline_metrics,
        candidate_metrics=candidate_metrics,
    )


def format_comparison_markdown(report: RunComparisonReport) -> str:
    """Human-readable comparison for review or CI logs."""
    lines = [
        "# Libby Run Comparison",
        "",
        f"- **Baseline**: `{report.baseline_run_id}` ({report.baseline_timestamp.isoformat()})",
        f"- **Candidate**: `{report.candidate_run_id}` ({report.candidate_timestamp.isoformat()})",
        f"- **Datasets**: {report.dataset_baseline} → {report.dataset_candidate}",
        "",
        "## Deltas",
        "",
        "| Metric | Delta |",
        "|--------|-------|",
        f"| Recommendations | {report.recommendation_count_delta:+d} |",
        f"| Clusters | {report.cluster_count_delta:+d} |",
        f"| Coherence | {report.coherence_delta:+.4f} |",
        f"| Extraction coverage | {report.extraction_coverage_delta:+.4f} |",
        f"| Likely false positives | {report.false_positive_delta:+d} |",
        f"| Cluster stability | {report.cluster_stability_score:.4f} |",
        f"| Recommendation churn | {report.recommendation_churn_rate:.4f} |",
        f"| Repeat recommendations | {report.repeat_recommendation_rate:.4f} |",
        "",
    ]
    if report.notable_changes:
        lines.append("## Notable changes")
        lines.append("")
        for note in report.notable_changes:
            lines.append(f"- {note}")
        lines.append("")
    if report.new_recommendations:
        lines.append("## New recommendations (candidate)")
        for title in report.new_recommendations[:10]:
            lines.append(f"- {title}")
        lines.append("")
    if report.removed_recommendations:
        lines.append("## Removed recommendations (vs baseline)")
        for title in report.removed_recommendations[:10]:
            lines.append(f"- {title}")
        lines.append("")
    return "\n".join(lines)
