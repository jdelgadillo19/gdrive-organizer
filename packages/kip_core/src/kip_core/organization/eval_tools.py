"""Utilities for inspecting clusters and tuning organizational intelligence."""

from __future__ import annotations

from dataclasses import dataclass

from kip_core.organization.clustering import cluster_documents, pairwise_similarity_debug
from kip_core.organization.embeddings import CorpusSemanticModel, fit_corpus_embeddings
from kip_core.organization.models import (
    DocumentCluster,
    DocumentProfile,
    OrganizationAnalysisResult,
    RecommendationType,
)
from kip_core.organization.recommendation_filtering import relocation_usefulness_score


@dataclass(frozen=True)
class ClusterInspectionReport:
    cluster_id: str
    label: str
    member_count: int
    cohesion_score: float
    relationship_type: str
    operational_role: str
    shared_signals: list[str]
    similarity_breakdown: dict[str, float]


@dataclass(frozen=True)
class RecommendationUsefulnessReport:
    recommendation_id: str
    recommendation_type: str
    title: str
    confidence_score: float
    usefulness_estimate: float | None
    likely_false_positive: bool
    rationale_preview: str


def inspect_clusters(clusters: list[DocumentCluster]) -> list[ClusterInspectionReport]:
    return [
        ClusterInspectionReport(
            cluster_id=c.cluster_id,
            label=c.label,
            member_count=len(c.member_file_ids),
            cohesion_score=c.cohesion_score,
            relationship_type=c.relationship_type.value,
            operational_role=c.operational_role.value,
            shared_signals=list(c.shared_signals),
            similarity_breakdown=c.similarity_breakdown.model_dump(),
        )
        for c in clusters
    ]


def debug_semantic_similarity(
    profiles: list[DocumentProfile],
    file_id_a: str,
    file_id_b: str,
) -> dict[str, float | str]:
    """Return decomposed similarity between two documents for tuning."""
    model: CorpusSemanticModel = fit_corpus_embeddings(profiles)
    profile_a = next(p for p in profiles if p.file_id == file_id_a)
    profile_b = next(p for p in profiles if p.file_id == file_id_b)
    return pairwise_similarity_debug(profile_a, profile_b, model=model)


def evaluate_recommendation_usefulness(
    result: OrganizationAnalysisResult,
    *,
    profiles: list[DocumentProfile] | None = None,
) -> list[RecommendationUsefulnessReport]:
    """Flag recommendations that may be low-value or false positives."""
    profile_by_id = {p.file_id: p for p in (profiles or [])}
    cluster_by_id = {c.cluster_id: c for c in result.clusters}
    folder_by_cluster = {f.cluster_id: f for f in result.proposed_folders if f.cluster_id}

    reports: list[RecommendationUsefulnessReport] = []
    extraction_ratio = _extraction_ratio(result)

    for rec in result.recommendations:
        usefulness: float | None = None
        false_positive = False

        if rec.recommendation_type == RecommendationType.FILE_MOVE:
            cluster = cluster_by_id.get(rec.cluster_id or "")
            folder = folder_by_cluster.get(rec.cluster_id or "")
            if cluster and folder:
                usefulness = relocation_usefulness_score(
                    cluster=cluster,
                    folder=folder,
                    profiles=list(profile_by_id.values()),
                    extraction_ratio=extraction_ratio,
                    structure=result.structure_assessment,
                )
                false_positive = usefulness < result.preferences.min_usefulness_score
        elif rec.recommendation_type == RecommendationType.FILE_RENAME:
            usefulness = rec.confidence_score
            false_positive = rec.confidence_level.value == "low" and len(
                rec.metadata.get("signals", [])
            ) < 2

        reports.append(
            RecommendationUsefulnessReport(
                recommendation_id=rec.id,
                recommendation_type=rec.recommendation_type.value,
                title=rec.title,
                confidence_score=rec.confidence_score,
                usefulness_estimate=usefulness,
                likely_false_positive=false_positive,
                rationale_preview=rec.rationale[:120],
            )
        )
    return reports


def format_cluster_report(clusters: list[DocumentCluster]) -> str:
    lines = ["Cluster inspection", "=" * 40]
    for row in inspect_clusters(clusters):
        lines.append(
            f"- {row.label} ({row.member_count} files) "
            f"cohesion={row.cohesion_score:.2f} "
            f"role={row.operational_role} rel={row.relationship_type}"
        )
        if row.shared_signals:
            lines.append(f"  signals: {', '.join(row.shared_signals[:6])}")
    return "\n".join(lines)


def _extraction_ratio(result: OrganizationAnalysisResult) -> float:
    total = result.document_count or 1
    ok = result.extraction_summary.get("success", 0) + result.extraction_summary.get(
        "partial", 0
    )
    return round(ok / total, 4)


def recluster_for_debug(
    profiles: list[DocumentProfile],
    *,
    similarity_threshold: float = 0.32,
) -> list[DocumentCluster]:
    """Re-run clustering with explicit threshold for offline tuning."""
    return cluster_documents(profiles, similarity_threshold=similarity_threshold)
