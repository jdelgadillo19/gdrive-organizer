"""Folder structure quality assessment and hierarchy recommendations."""

from __future__ import annotations

import re
from collections import defaultdict

from kip_core.organization.models import (
    AnalysisPreferences,
    DocumentCluster,
    DocumentProfile,
    ExistingStructureAssessment,
    FolderSelection,
    ProposedFolder,
)

_MESSY_NAME_RE = re.compile(
    r"(copy|final|v\d+|untitled|misc|temp|old|new\s+\d+|\(\d+\))",
    re.IGNORECASE,
)


def _path_depth(relative_path: str) -> int:
    parts = [p for p in relative_path.split("/") if p]
    return max(0, len(parts) - 1)


def assess_existing_structure(
    profiles: list[DocumentProfile],
    *,
    selection: FolderSelection,
) -> ExistingStructureAssessment:
    """Score whether the current layout is already coherent enough to preserve."""
    if not profiles:
        return ExistingStructureAssessment(
            root_folder_id=selection.root_folder_id,
            coherence_score=1.0,
            is_well_organized=True,
            rationale="No documents in scope; existing structure requires no changes.",
        )

    folder_groups: dict[str, list[DocumentProfile]] = defaultdict(list)
    for profile in profiles:
        folder_key = "/".join(profile.folder_segments) if profile.folder_segments else "(root)"
        folder_groups[folder_key].append(profile)

    issues: list[str] = []
    well_organized_paths: list[str] = []
    folder_scores: list[float] = []

    for folder_path, members in folder_groups.items():
        if folder_path == "(root)" and len(members) > 8:
            issues.append("root contains many loose files; shallow grouping may help")
            folder_scores.append(0.35)
            continue

        messy_names = sum(1 for m in members if _MESSY_NAME_RE.search(m.name))
        messy_ratio = messy_names / len(members)
        depth_penalty = 0.1 if _path_depth(members[0].relative_path) > 4 else 0.0
        folder_score = max(0.0, 1.0 - messy_ratio - depth_penalty)
        folder_scores.append(folder_score)

        if folder_score >= 0.75 and len(members) >= 2:
            well_organized_paths.append(folder_path)
        elif messy_ratio > 0.4:
            issues.append(f'folder "{folder_path}" has inconsistent or noisy filenames')

    coherence_score = sum(folder_scores) / len(folder_scores) if folder_scores else 0.5
    is_well_organized = coherence_score >= 0.72 and len(issues) <= 1

    rationale = (
        "Existing folders appear coherent; Libby will prefer minimal structural changes."
        if is_well_organized
        else (
            "Existing layout shows mixed naming and loose grouping; "
            "targeted folders are suggested."
        )
    )

    return ExistingStructureAssessment(
        root_folder_id=selection.root_folder_id,
        coherence_score=round(coherence_score, 4),
        is_well_organized=is_well_organized,
        well_organized_paths=sorted(well_organized_paths),
        issues=issues,
        rationale=rationale,
    )


def infer_proposed_folders(
    clusters: list[DocumentCluster],
    profiles: list[DocumentProfile],
    assessment: ExistingStructureAssessment,
    preferences: AnalysisPreferences,
) -> list[ProposedFolder]:
    """Propose shallow semantic folders; skip clusters already in coherent paths."""
    profile_by_id = {p.file_id: p for p in profiles}
    proposed: list[ProposedFolder] = []

    for cluster in clusters:
        members = [profile_by_id[fid] for fid in cluster.member_file_ids if fid in profile_by_id]
        if not members:
            continue

        if preferences.preserve_existing_coherent_folders and assessment.is_well_organized:
            shared_folder = members[0].folder_segments[0] if members[0].folder_segments else None
            if shared_folder and shared_folder in {
                p.split("/")[0] if p != "(root)" else p for p in assessment.well_organized_paths
            }:
                continue

        if cluster.cohesion_score < preferences.min_relocation_cohesion:
            continue
        if len(members) < preferences.min_cluster_size_for_relocation:
            continue

        slug = _folder_slug(cluster.label, cluster.top_keywords, cluster.operational_role.value)
        target_path = slug
        if _path_depth(target_path) > preferences.max_proposed_depth:
            target_path = "/".join(target_path.split("/")[: preferences.max_proposed_depth])

        needs_relocation = any(
            not m.folder_segments or m.folder_segments[0] != slug for m in members
        )
        if not needs_relocation and len(members) < 2:
            continue

        proposed.append(
            ProposedFolder(
                path=target_path,
                label=cluster.label,
                cluster_id=cluster.cluster_id,
                member_file_ids=cluster.member_file_ids,
            )
        )

    return proposed


def _folder_slug(label: str, keywords: list[str], operational_role: str = "") -> str:
    if operational_role and operational_role not in ("unknown", "general"):
        role_slug = re.sub(r"[^a-z0-9]+", "-", operational_role.lower()).strip("-")
        if role_slug:
            return role_slug
    source = keywords[0] if keywords else label
    cleaned = re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")
    return cleaned or "organized-documents"
