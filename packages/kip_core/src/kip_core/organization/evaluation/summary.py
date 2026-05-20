"""Human-readable markdown summaries for analysis artifact review."""

from __future__ import annotations

from kip_core.organization.eval_tools import evaluate_recommendation_usefulness
from kip_core.organization.evaluation.comparison import format_comparison_markdown
from kip_core.organization.evaluation.models import RunComparisonReport, RunMetrics
from kip_core.organization.models import DocumentProfile, OrganizationAnalysisResult


def render_summary_markdown(
    result: OrganizationAnalysisResult,
    metrics: RunMetrics,
    *,
    profiles: list[DocumentProfile] | None = None,
    comparison: RunComparisonReport | None = None,
) -> str:
    """Generate a human review summary for a single analysis run."""
    usefulness = evaluate_recommendation_usefulness(result, profiles=profiles)
    flagged = [u for u in usefulness if u.likely_false_positive]
    top_recs = sorted(
        result.recommendations,
        key=lambda r: r.confidence_score,
        reverse=True,
    )[:12]
    clusters_sorted = sorted(
        result.clusters,
        key=lambda c: len(c.member_file_ids),
        reverse=True,
    )[:8]

    lines = [
        "# Libby Analysis Summary",
        "",
        f"- **Run ID**: `{metrics.run_id}`",
        f"- **Dataset**: {metrics.dataset_name} (`{metrics.dataset_slug}`)",
        f"- **Timestamp**: {metrics.timestamp.isoformat()}",
        f"- **Engine hash**: `{metrics.engine_version_hash}`",
        f"- **Source**: {metrics.source_folder or 'N/A'}",
        "",
        "## Scope",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Documents analyzed | {metrics.document_count} |",
        f"| Scanned items | {metrics.scanned_item_count} |",
        f"| Clusters | {metrics.cluster_count} |",
        f"| Recommendations | {metrics.recommendation_counts.total} |",
        f"| Structure coherence | {metrics.structure_coherence_score:.4f} |",
        f"| Well organized | {metrics.is_well_organized} |",
        f"| Avg cluster cohesion | {metrics.average_cluster_cohesion:.4f} |",
        "",
        "## Extraction coverage",
        "",
    ]
    for status, count in sorted(metrics.extraction.summary.items()):
        lines.append(f"- **{status}**: {count}")
    lines.extend(
        [
            f"- **Coverage ratio**: {metrics.extraction.coverage_ratio:.2%}",
            f"- **Avg extraction confidence**: "
            f"{metrics.extraction.average_extraction_confidence:.4f}",
            "",
            "## Recommendation quality",
            "",
            f"- **Likely false positives**: {metrics.false_positives.likely_false_positive_count} "
            f"({metrics.false_positives.false_positive_rate:.1%})",
            f"- **Avg usefulness**: {metrics.quality_summary.get('average_usefulness', 0):.4f}",
            f"- **Suppressed relocations (est.)**: "
            f"{metrics.suppression.estimated_suppressed_relocations}",
            "",
            "## Semantic configuration",
            "",
            f"- **Embedder**: {metrics.semantic_configuration.embedder}",
            f"- **Similarity threshold**: {metrics.semantic_configuration.similarity_threshold}",
            f"- **Hybrid weights**: {metrics.semantic_configuration.hybrid_weights}",
            "",
            "## Largest semantic clusters",
            "",
        ]
    )
    for cluster in clusters_sorted:
        lines.append(
            f"- **{cluster.label}** ({len(cluster.member_file_ids)} files) — "
            f"cohesion {cluster.cohesion_score:.2f}, "
            f"{cluster.relationship_type.value}, role `{cluster.operational_role.value}`"
        )
        if cluster.shared_signals:
            lines.append(f"  - Signals: {', '.join(cluster.shared_signals[:5])}")

    lines.extend(["", "## Key recommendations", ""])
    for rec in top_recs:
        lines.append(
            f"- [{rec.confidence_level.value}] **{rec.title}** — {rec.rationale[:100]}"
        )

    if flagged:
        lines.extend(["", "## Likely false positives", ""])
        for row in flagged[:12]:
            lines.append(
                f"- {row.title} (usefulness={row.usefulness_estimate}, "
                f"confidence={row.confidence_score:.2f})"
            )

    if metrics.stability.prior_run_id:
        prior_id = metrics.stability.prior_run_id
        lines.extend(["", "## Changes vs prior run", "", f"- **Prior run**: `{prior_id}`"])
        if metrics.stability.cluster_stability_score is not None:
            lines.append(
                f"- **Cluster stability**: {metrics.stability.cluster_stability_score:.4f}"
            )
        if metrics.stability.recommendation_churn_rate is not None:
            lines.append(
                f"- **Recommendation churn**: "
                f"{metrics.stability.recommendation_churn_rate:.4f}"
            )
        if metrics.stability.repeat_recommendation_rate is not None:
            lines.append(
                f"- **Repeat rate**: {metrics.stability.repeat_recommendation_rate:.4f}"
            )
        if metrics.stability.false_positive_delta is not None:
            lines.append(
                f"- **False positive delta**: {metrics.stability.false_positive_delta:+d}"
            )
        if metrics.stability.coherence_delta is not None:
            lines.append(
                f"- **Coherence delta**: {metrics.stability.coherence_delta:+.4f}"
            )
        if metrics.stability.extraction_coverage_delta is not None:
            lines.append(
                f"- **Extraction delta**: "
                f"{metrics.stability.extraction_coverage_delta:+.4f}"
            )

    if comparison:
        lines.extend(["", "---", "", format_comparison_markdown(comparison)])

    if result.structure_assessment.issues:
        lines.extend(["", "## Structure issues", ""])
        for issue in result.structure_assessment.issues[:8]:
            lines.append(f"- {issue}")

    lines.append("")
    return "\n".join(lines)
