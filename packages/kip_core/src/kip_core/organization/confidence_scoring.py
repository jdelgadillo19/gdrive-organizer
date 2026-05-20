"""Confidence scoring for organizational recommendations."""

from __future__ import annotations

from kip_core.organization.models import (
    ConfidenceLevel,
    DocumentCluster,
    ExistingStructureAssessment,
)


def score_to_level(score: float) -> ConfidenceLevel:
    if score >= 0.75:
        return ConfidenceLevel.HIGH
    if score >= 0.5:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def cluster_confidence(cluster: DocumentCluster, extraction_ratio: float) -> float:
    """Cluster relocation confidence from cohesion, semantics, and extraction coverage."""
    semantic = cluster.similarity_breakdown.semantic_score
    base = cluster.cohesion_score * 0.45 + semantic * 0.25 + extraction_ratio * 0.2
    if cluster.relationship_type.value == "shared_operational_role":
        base += 0.06
    if len(cluster.member_file_ids) == 1:
        base *= 0.55
    elif len(cluster.member_file_ids) < 3:
        base *= 0.85
    return round(min(1.0, max(0.0, base)), 4)


def rename_confidence(signals: list[str], extraction_ratio: float) -> float:
    """Rename confidence from detected normalization signals."""
    signal_boost = min(0.35, len(signals) * 0.08)
    base = 0.45 + signal_boost + extraction_ratio * 0.2
    return round(min(1.0, max(0.0, base)), 4)


def preserve_structure_confidence(assessment: ExistingStructureAssessment) -> float:
    return round(min(1.0, assessment.coherence_score), 4)


def extraction_coverage_ratio(successful_extractions: int, total_documents: int) -> float:
    if total_documents == 0:
        return 0.0
    return round(successful_extractions / total_documents, 4)


def apply_conservative_cap(
    score: float,
    *,
    prefer_minimal_changes: bool,
    structure_is_coherent: bool,
    usefulness: float | None = None,
) -> float:
    """Reduce aggressive recommendations when existing structure is already good."""
    capped = score
    if prefer_minimal_changes and structure_is_coherent:
        capped = min(capped, 0.58)
    if usefulness is not None and usefulness < 0.45:
        capped = min(capped, 0.48)
    return round(min(1.0, max(0.0, capped)), 4)


def suppress_low_confidence(score: float, *, min_score: float = 0.48) -> bool:
    """Whether a recommendation should be omitted entirely."""
    return score < min_score
