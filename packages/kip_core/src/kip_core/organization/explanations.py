"""Human-readable recommendation explanations with semantic signal detail."""

from __future__ import annotations

from kip_core.organization.models import (
    DocumentCluster,
    DocumentProfile,
    ExistingStructureAssessment,
    ProposedFolder,
    SimilarityBreakdown,
)


def explain_cluster_grouping(cluster: DocumentCluster, member_names: list[str]) -> tuple[str, str]:
    """Return (rationale, detailed_explanation) for a semantic cluster."""
    signals = ", ".join(cluster.shared_signals[:5]) or "path and filename context"
    relationship = cluster.relationship_type.value.replace("_", " ")
    sample_names = ", ".join(member_names[:3])
    if len(member_names) > 3:
        sample_names += f", and {len(member_names) - 3} more"

    rationale = (
        f"Grouped {len(member_names)} document(s) by {relationship}: {signals}."
    )
    breakdown = cluster.similarity_breakdown
    detailed = (
        f"Libby detected {relationship} across: {sample_names}. "
        f"Semantic similarity {breakdown.semantic_score:.2f}, "
        f"lexical overlap {breakdown.lexical_score:.2f}, "
        f"context alignment {breakdown.context_score:.2f}. "
    )
    if cluster.distinguishing_signals:
        detailed += (
            f"Distinguishing signals (not mere keyword overlap): "
            f"{', '.join(cluster.distinguishing_signals[:4])}. "
        )
    if cluster.operational_role.value not in ("unknown", "general"):
        detailed += f"Inferred operational role: {cluster.operational_role.value}. "
    detailed += "No files will be moved until you explicitly approve."
    return rationale, detailed


def explain_move_recommendation(
    *,
    cluster: DocumentCluster | None,
    folder: ProposedFolder,
    profile: DocumentProfile,
    structure: ExistingStructureAssessment,
) -> tuple[str, str]:
    cohesion = cluster.cohesion_score if cluster else 0.5
    rel = (
        cluster.relationship_type.value.replace("_", " ")
        if cluster
        else "semantic context"
    )
    rationale = (
        f"Move '{profile.name}' into '{folder.path}/' — "
        f"{len(folder.member_file_ids)} related file(s) share {rel}."
    )
    if structure.is_well_organized:
        structure_note = (
            "Existing folder layout is partially coherent; "
            "this targets loose or mixed files only."
        )
    else:
        structure_note = (
            "Existing layout shows mixed grouping; "
            "this consolidation should improve discoverability."
        )
    breakdown: SimilarityBreakdown = (
        cluster.similarity_breakdown if cluster else SimilarityBreakdown()
    )
    detailed = (
        f"Destination '{folder.path}' groups documents with cohesion {cohesion:.2f}. "
        f"Signals — semantic: {breakdown.semantic_score:.2f}, "
        f"lexical: {breakdown.lexical_score:.2f}, context: {breakdown.context_score:.2f}. "
        f"{structure_note} "
        "Approval is required before any move is applied."
    )
    return rationale, detailed


def explain_rename_recommendation(
    *,
    original_name: str,
    proposed_name: str,
    signals: list[str],
    profile: DocumentProfile,
    cluster_label: str | None,
) -> tuple[str, str]:
    signal_text = ", ".join(signals) if signals else "general filename cleanup"
    rationale = (
        f"Normalize '{original_name}' → '{proposed_name}' for naming consistency "
        f"({profile.operational_role.value} document)."
    )
    cluster_part = f" Aligns with cluster '{cluster_label}'." if cluster_label else ""
    detailed = (
        f"Rename improves scanability: {signal_text}.{cluster_part} "
        f"Extraction confidence {profile.extraction_confidence:.2f}. "
        "Extension and document identity are preserved; approval required."
    )
    return rationale, detailed


def explain_preserve_structure(assessment: ExistingStructureAssessment) -> tuple[str, str]:
    paths = ", ".join(assessment.well_organized_paths[:4]) or "current folders"
    detailed = (
        f"Coherence score {assessment.coherence_score:.2f}. "
        f"Well-organized areas include: {paths}. "
        "Libby will avoid aggressive restructuring and limit proposals to "
        "high-value filename cleanup or clearly loose files."
    )
    return assessment.rationale, detailed


def explain_weak_structure_issue(assessment: ExistingStructureAssessment) -> str:
    if not assessment.issues:
        return "No major structural weaknesses detected."
    return "; ".join(assessment.issues[:3])
