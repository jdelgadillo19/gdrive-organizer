"""Organizational recommendation assembly and explanation generation."""

from __future__ import annotations

from kip_core.organization.analyzer import (
    assess_scan_coverage,
    build_document_profiles,
    extraction_summary,
    scan_items,
)
from kip_core.organization.clustering import cluster_documents
from kip_core.organization.confidence_scoring import (
    apply_conservative_cap,
    cluster_confidence,
    extraction_coverage_ratio,
    preserve_structure_confidence,
    rename_confidence,
    score_to_level,
    suppress_low_confidence,
)
from kip_core.organization.explanations import (
    explain_move_recommendation,
    explain_preserve_structure,
    explain_rename_recommendation,
    explain_weak_structure_issue,
)
from kip_core.organization.models import (
    AnalysisPreferences,
    ConfidenceLevel,
    ExtractionStatus,
    FolderSelection,
    OrganizationAnalysisResult,
    OrganizationRecommendation,
    RecommendationType,
    RollbackMetadata,
    ScannedDriveItem,
)
from kip_core.organization.recommendation_filtering import (
    dedupe_and_cap_recommendations,
    relocation_usefulness_score,
    should_propose_relocation,
    should_propose_rename,
)
from kip_core.organization.rename_rules import propose_renames_for_profiles
from kip_core.organization.structure_inference import (
    assess_existing_structure,
    infer_proposed_folders,
)


def run_organizational_analysis(
    selection: FolderSelection,
    items: list[ScannedDriveItem],
    preferences: AnalysisPreferences | None = None,
) -> OrganizationAnalysisResult:
    """
    End-to-end organizational intelligence pipeline.

    1. Recursive scan inventory (caller-provided items)
    2. Content extraction and profiling
    3. Semantic clustering (embedding + lexical + context)
    4. Structure inference
    5. Rename normalization
    6. Recommendation + explanation generation
    7. Confidence scoring, usefulness filtering, rollback metadata
    """
    prefs = preferences or AnalysisPreferences()
    _folders, documents = scan_items(items)
    profiles = build_document_profiles(documents, selection=selection)
    ext_summary = extraction_summary(profiles)
    successful = ext_summary.get(ExtractionStatus.SUCCESS.value, 0) + ext_summary.get(
        ExtractionStatus.PARTIAL.value, 0
    )
    extraction_ratio = extraction_coverage_ratio(successful, len(profiles))

    structure = assess_existing_structure(profiles, selection=selection)
    scan_issues = assess_scan_coverage(documents, profiles)
    structure.issues.extend(scan_issues)

    clusters = cluster_documents(profiles)
    proposed_folders = infer_proposed_folders(clusters, profiles, structure, prefs)

    cluster_label_by_file = {
        file_id: cluster.label
        for cluster in clusters
        for file_id in cluster.member_file_ids
    }
    cluster_by_id = {c.cluster_id: c for c in clusters}

    recommendations: list[OrganizationRecommendation] = []

    if structure.is_well_organized and prefs.preserve_existing_coherent_folders:
        preserve_score = preserve_structure_confidence(structure)
        rationale, detailed = explain_preserve_structure(structure)
        recommendations.append(
            OrganizationRecommendation(
                recommendation_type=RecommendationType.PRESERVE_STRUCTURE,
                title="Preserve existing folder organization",
                rationale=rationale,
                detailed_explanation=detailed,
                confidence_score=preserve_score,
                confidence_level=score_to_level(preserve_score),
                impacted_file_ids=[p.file_id for p in profiles],
                rollback=RollbackMetadata(
                    operation_type="preserve",
                    file_id=selection.root_folder_id,
                    original_path=selection.root_folder_name,
                    original_name=selection.root_folder_name,
                    proposed_path=selection.root_folder_name,
                    proposed_name=selection.root_folder_name,
                ),
            )
        )

    structure_weakness = explain_weak_structure_issue(structure)

    if prefs.enable_relocation_recommendations:
        for folder in proposed_folders:
            cluster = cluster_by_id.get(folder.cluster_id or "")
            if not should_propose_relocation(
                cluster=cluster,
                folder=folder,
                profiles=profiles,
                prefs=prefs,
                structure=structure,
                extraction_ratio=extraction_ratio,
            ):
                continue

            cohesion = cluster.cohesion_score if cluster else 0.5
            raw_score = cluster_confidence(cluster, extraction_ratio) if cluster else 0.45
            usefulness = relocation_usefulness_score(
                cluster=cluster,
                folder=folder,
                profiles=profiles,
                extraction_ratio=extraction_ratio,
                structure=structure,
            )
            score = apply_conservative_cap(
                raw_score,
                prefer_minimal_changes=prefs.prefer_minimal_changes,
                structure_is_coherent=structure.is_well_organized,
                usefulness=usefulness,
            )
            level = score_to_level(score)
            if prefs.prefer_minimal_changes and (
                level == ConfidenceLevel.LOW or suppress_low_confidence(score)
            ):
                continue

            for file_id in folder.member_file_ids:
                profile = next((p for p in profiles if p.file_id == file_id), None)
                if profile is None:
                    continue
                rationale, detailed = explain_move_recommendation(
                    cluster=cluster,
                    folder=folder,
                    profile=profile,
                    structure=structure,
                )
                if structure_weakness and structure_weakness not in detailed:
                    detailed += f" Structure note: {structure_weakness}"
                recommendations.append(
                    OrganizationRecommendation(
                        recommendation_type=RecommendationType.FILE_MOVE,
                        title=f"Move '{profile.name}' to '{folder.path}/'",
                        rationale=rationale,
                        detailed_explanation=detailed,
                        confidence_score=score,
                        confidence_level=level,
                        impacted_file_ids=[file_id],
                        proposed_destination_path=folder.path,
                        cluster_id=folder.cluster_id,
                        rollback=RollbackMetadata(
                            operation_type="move",
                            file_id=file_id,
                            original_path=profile.relative_path,
                            original_name=profile.name,
                            proposed_path=f"{folder.path}/{profile.name}",
                            proposed_name=profile.name,
                            parent_folder_id=profile.parent_folder_id,
                        ),
                        metadata={
                            "cohesion": cohesion,
                            "cluster_label": folder.label,
                            "usefulness": usefulness,
                            "relationship_type": (
                                cluster.relationship_type.value if cluster else None
                            ),
                        },
                    )
                )

    if prefs.enable_rename_recommendations:
        rename_proposals = propose_renames_for_profiles(profiles, cluster_label_by_file)
        for proposal in rename_proposals:
            raw_score = rename_confidence(proposal.signals, extraction_ratio)
            score = apply_conservative_cap(
                raw_score,
                prefer_minimal_changes=prefs.prefer_minimal_changes,
                structure_is_coherent=structure.is_well_organized,
            )
            level = score_to_level(score)
            if not should_propose_rename(
                signal_count=len(proposal.signals),
                confidence_level=level,
                prefs=prefs,
            ):
                continue
            if prefs.prefer_minimal_changes and suppress_low_confidence(score, min_score=0.5):
                continue

            profile = next(p for p in profiles if p.file_id == proposal.file_id)
            cluster_label = cluster_label_by_file.get(proposal.file_id)
            rationale, detailed = explain_rename_recommendation(
                original_name=proposal.original_name,
                proposed_name=proposal.proposed_name,
                signals=proposal.signals,
                profile=profile,
                cluster_label=cluster_label,
            )
            recommendations.append(
                OrganizationRecommendation(
                    recommendation_type=RecommendationType.FILE_RENAME,
                    title=f"Rename '{proposal.original_name}' → '{proposal.proposed_name}'",
                    rationale=rationale,
                    detailed_explanation=detailed,
                    confidence_score=score,
                    confidence_level=level,
                    impacted_file_ids=[proposal.file_id],
                    proposed_name=proposal.proposed_name,
                    rollback=RollbackMetadata(
                        operation_type="rename",
                        file_id=proposal.file_id,
                        original_path=profile.relative_path,
                        original_name=proposal.original_name,
                        proposed_path=profile.relative_path,
                        proposed_name=proposal.proposed_name,
                        parent_folder_id=profile.parent_folder_id,
                    ),
                    metadata={"signals": proposal.signals},
                )
            )

    for folder in proposed_folders:
        cluster = cluster_by_id.get(folder.cluster_id or "")
        if not should_propose_relocation(
            cluster=cluster,
            folder=folder,
            profiles=profiles,
            prefs=prefs,
            structure=structure,
            extraction_ratio=extraction_ratio,
        ):
            continue
        if any(
            r.recommendation_type == RecommendationType.FOLDER_CREATE
            and r.proposed_destination_path == folder.path
            for r in recommendations
        ):
            continue
        score = apply_conservative_cap(
            cluster_confidence(cluster, extraction_ratio) if cluster else 0.5,
            prefer_minimal_changes=prefs.prefer_minimal_changes,
            structure_is_coherent=structure.is_well_organized,
        )
        rel = cluster.relationship_type.value.replace("_", " ") if cluster else "semantic"
        shared = (
            ", ".join((cluster.shared_signals if cluster else [])[:4])
            or "contextual similarity"
        )
        cohesion_val = cluster.cohesion_score if cluster else 0.0
        recommendations.append(
            OrganizationRecommendation(
                recommendation_type=RecommendationType.FOLDER_CREATE,
                title=f"Create folder '{folder.path}'",
                rationale=(
                    f"Introduce folder '{folder.path}' to group {len(folder.member_file_ids)} "
                    f"documents sharing {rel} ({folder.label})."
                ),
                detailed_explanation=(
                    f"Folder creation is proposed before any file moves. "
                    f"Cluster cohesion {cohesion_val:.2f}. "
                    f"Shared signals: {shared}. "
                    "You can approve folder creation independently from relocations."
                ),
                confidence_score=score,
                confidence_level=score_to_level(score),
                impacted_file_ids=folder.member_file_ids,
                proposed_destination_path=folder.path,
                cluster_id=folder.cluster_id,
                rollback=RollbackMetadata(
                    operation_type="folder_create",
                    file_id=selection.root_folder_id,
                    original_path=selection.root_folder_name,
                    original_name=selection.root_folder_name,
                    proposed_path=folder.path,
                    proposed_name=folder.path,
                ),
            )
        )

    recommendations = dedupe_and_cap_recommendations(recommendations, prefs)

    return OrganizationAnalysisResult(
        selection=selection,
        preferences=prefs,
        scanned_item_count=len(items),
        document_count=len(profiles),
        extraction_summary=ext_summary,
        structure_assessment=structure,
        clusters=clusters,
        proposed_folders=proposed_folders,
        recommendations=recommendations,
    )
