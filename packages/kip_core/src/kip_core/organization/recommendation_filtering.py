"""Usefulness thresholds and anti-overorganization heuristics."""

from __future__ import annotations

from kip_core.organization.models import (
    AnalysisPreferences,
    ConfidenceLevel,
    DocumentCluster,
    DocumentProfile,
    ExistingStructureAssessment,
    OrganizationRecommendation,
    ProposedFolder,
    RecommendationType,
)
from kip_core.organization.semantic_features import average_extraction_confidence


def relocation_usefulness_score(
    *,
    cluster: DocumentCluster | None,
    folder: ProposedFolder,
    profiles: list[DocumentProfile],
    extraction_ratio: float,
    structure: ExistingStructureAssessment,
) -> float:
    """Score whether a relocation recommendation adds organizational value."""
    if cluster is None:
        return 0.3
    member_profiles = [p for p in profiles if p.file_id in folder.member_file_ids]
    if not member_profiles:
        return 0.0

    already_grouped = sum(
        1
        for p in member_profiles
        if p.folder_segments and p.folder_segments[0] == folder.path.split("/")[0]
    )
    grouping_ratio = already_grouped / len(member_profiles)
    anti_overorg_penalty = 0.25 * grouping_ratio if structure.is_well_organized else 0.0

    size_factor = min(1.0, len(folder.member_file_ids) / 4)
    cohesion = cluster.cohesion_score
    extraction = average_extraction_confidence(member_profiles) * 0.5 + extraction_ratio * 0.5
    role_bonus = 0.08 if cluster.relationship_type.value == "shared_operational_role" else 0.0

    raw = (
        cohesion * 0.45
        + size_factor * 0.25
        + extraction * 0.2
        + role_bonus
        - anti_overorg_penalty
    )
    return round(max(0.0, min(1.0, raw)), 4)


def should_propose_relocation(
    *,
    cluster: DocumentCluster | None,
    folder: ProposedFolder,
    profiles: list[DocumentProfile],
    prefs: AnalysisPreferences,
    structure: ExistingStructureAssessment,
    extraction_ratio: float,
) -> bool:
    if len(folder.member_file_ids) < prefs.min_cluster_size_for_relocation:
        return False
    cohesion = cluster.cohesion_score if cluster else 0.0
    if cohesion < prefs.min_relocation_cohesion:
        return False
    usefulness = relocation_usefulness_score(
        cluster=cluster,
        folder=folder,
        profiles=profiles,
        extraction_ratio=extraction_ratio,
        structure=structure,
    )
    if usefulness < prefs.min_usefulness_score:
        return False
    if structure.is_well_organized and prefs.preserve_existing_coherent_folders:
        member_profiles = [p for p in profiles if p.file_id in folder.member_file_ids]
        if member_profiles and all(
            p.folder_segments and p.folder_segments[0] in structure.well_organized_paths
            for p in member_profiles
        ):
            return False
    return True


def should_propose_rename(
    *,
    signal_count: int,
    confidence_level: ConfidenceLevel,
    prefs: AnalysisPreferences,
) -> bool:
    if signal_count == 0:
        return False
    if prefs.prefer_minimal_changes and confidence_level == ConfidenceLevel.LOW:
        return False
    return True


def dedupe_and_cap_recommendations(
    recommendations: list[OrganizationRecommendation],
    prefs: AnalysisPreferences,
) -> list[OrganizationRecommendation]:
    """Limit noisy duplicates and cap recommendation volume."""
    moves = [
        r
        for r in recommendations
        if r.recommendation_type == RecommendationType.FILE_MOVE
    ]
    renames = [
        r
        for r in recommendations
        if r.recommendation_type == RecommendationType.FILE_RENAME
    ]
    others = [
        r
        for r in recommendations
        if r.recommendation_type
        not in (RecommendationType.FILE_MOVE, RecommendationType.FILE_RENAME)
    ]

    moves_sorted = sorted(moves, key=lambda r: r.confidence_score, reverse=True)
    renames_sorted = sorted(renames, key=lambda r: r.confidence_score, reverse=True)

    seen_move_targets: set[tuple[str, str]] = set()
    filtered_moves: list[OrganizationRecommendation] = []
    for rec in moves_sorted:
        if len(filtered_moves) >= prefs.max_relocation_recommendations:
            break
        dest = rec.proposed_destination_path or ""
        key = (dest, rec.impacted_file_ids[0] if rec.impacted_file_ids else "")
        if key in seen_move_targets:
            continue
        seen_move_targets.add(key)
        filtered_moves.append(rec)

    seen_renames: set[str] = set()
    filtered_renames: list[OrganizationRecommendation] = []
    for rec in renames_sorted:
        if len(filtered_renames) >= prefs.max_rename_recommendations:
            break
        file_id = rec.impacted_file_ids[0] if rec.impacted_file_ids else rec.id
        if file_id in seen_renames:
            continue
        seen_renames.add(file_id)
        filtered_renames.append(rec)

    return others + filtered_moves + filtered_renames
