"""Stability and churn metrics vs a prior analysis run."""

from __future__ import annotations

from kip_core.organization.evaluation.fingerprints import (
    cluster_fingerprint,
    cluster_member_sets,
    recommendation_fingerprint_set,
)
from kip_core.organization.evaluation.models import RunMetrics, StabilityMetrics
from kip_core.organization.models import DocumentCluster, OrganizationRecommendation


def cluster_stability_score(
    prior_clusters: list[DocumentCluster],
    candidate_clusters: list[DocumentCluster],
) -> float:
    """
    Best-match Jaccard overlap of member file sets between runs.

    Cluster IDs differ per run; matching is greedy on member overlap.
    """
    if not prior_clusters and not candidate_clusters:
        return 1.0
    if not prior_clusters or not candidate_clusters:
        return 0.0

    prior_sets = cluster_member_sets(prior_clusters)
    candidate_sets = cluster_member_sets(candidate_clusters)
    used: set[int] = set()
    overlaps: list[float] = []

    for pset in prior_sets:
        best_j = 0.0
        best_idx = -1
        for idx, cset in enumerate(candidate_sets):
            if idx in used:
                continue
            union = pset | cset
            if not union:
                continue
            jaccard = len(pset & cset) / len(union)
            if jaccard > best_j:
                best_j = jaccard
                best_idx = idx
        if best_idx >= 0:
            used.add(best_idx)
            overlaps.append(best_j)

    return round(sum(overlaps) / len(overlaps), 4) if overlaps else 0.0


def recommendation_churn(
    prior_recs: list[OrganizationRecommendation],
    candidate_recs: list[OrganizationRecommendation],
) -> tuple[float, float, set[str], set[str]]:
    """
    Return (churn_rate, repeat_rate, added_fps, removed_fps).
    """
    prior_fps = recommendation_fingerprint_set(prior_recs)
    candidate_fps = recommendation_fingerprint_set(candidate_recs)
    if not prior_fps and not candidate_fps:
        return 0.0, 1.0, set(), set()

    added = candidate_fps - prior_fps
    removed = prior_fps - candidate_fps
    union = prior_fps | candidate_fps
    churn = round(len(added | removed) / len(union), 4) if union else 0.0
    repeat = round(len(prior_fps & candidate_fps) / len(prior_fps), 4) if prior_fps else 0.0
    return churn, repeat, added, removed


def semantic_drift_inspection(
    prior_clusters: list[DocumentCluster],
    candidate_clusters: list[DocumentCluster],
) -> dict[str, object]:
    prior_fps = {cluster_fingerprint(c) for c in prior_clusters}
    candidate_fps = {cluster_fingerprint(c) for c in candidate_clusters}
    return {
        "prior_cluster_signatures": len(prior_fps),
        "candidate_cluster_signatures": len(candidate_fps),
        "stable_cluster_signatures": len(prior_fps & candidate_fps),
        "new_cluster_signatures": sorted(candidate_fps - prior_fps)[:10],
        "removed_cluster_signatures": sorted(prior_fps - candidate_fps)[:10],
    }


def compute_stability_vs_prior(
    *,
    prior_metrics: RunMetrics,
    prior_clusters: list[DocumentCluster],
    prior_recommendations: list[OrganizationRecommendation],
    candidate_clusters: list[DocumentCluster],
    candidate_recommendations: list[OrganizationRecommendation],
    candidate_fp_count: int,
    candidate_coherence: float,
    candidate_extraction_ratio: float,
    candidate_avg_usefulness: float,
) -> StabilityMetrics:
    stability_score = cluster_stability_score(prior_clusters, candidate_clusters)
    churn, repeat, _, _ = recommendation_churn(
        prior_recommendations, candidate_recommendations
    )
    prior_fp = prior_metrics.false_positives.likely_false_positive_count
    prior_coherence = prior_metrics.structure_coherence_score
    prior_extraction = prior_metrics.extraction.coverage_ratio
    prior_usefulness = prior_metrics.quality_summary.get("average_usefulness", 0.0)

    return StabilityMetrics(
        prior_run_id=prior_metrics.run_id,
        prior_run_timestamp=prior_metrics.timestamp,
        cluster_stability_score=stability_score,
        recommendation_churn_rate=churn,
        repeat_recommendation_rate=repeat,
        usefulness_trend_delta=round(candidate_avg_usefulness - prior_usefulness, 4),
        false_positive_delta=candidate_fp_count - prior_fp,
        coherence_delta=round(candidate_coherence - prior_coherence, 4),
        extraction_coverage_delta=round(
            candidate_extraction_ratio - prior_extraction, 4
        ),
    )
