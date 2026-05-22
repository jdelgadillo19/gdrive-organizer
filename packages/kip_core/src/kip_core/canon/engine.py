"""Canonization pipeline for local Drive export corpora."""

from __future__ import annotations

from pathlib import Path

from kip_core.canon.conflicts import (
    detect_cross_reference_issues,
    detect_near_duplicate_groups,
    detect_purpose_collisions,
)
from kip_core.canon.matcher import assign_topic, group_candidates_by_topic
from kip_core.canon.models import (
    CanonDocumentCandidate,
    CanonizationResult,
    CanonTopicId,
    CanonTopicResult,
)
from kip_core.canon.scan import resolve_corpus_root, scan_local_folder
from kip_core.canon.topics import CANON_TOPICS
from kip_core.domain.governance import AuthorityLevel
from kip_core.organization.analyzer import build_document_profiles, scan_items
from kip_core.organization.models import ExtractionStatus, FolderSelection


def run_canonization(
    corpus_path: Path,
    *,
    canon_folder_relative: str = "Canon",
) -> CanonizationResult:
    """Analyze corpus, assign canon topics, detect conflicts, recommend promotions."""
    root = resolve_corpus_root(corpus_path)
    selection = FolderSelection(root_folder_id=str(root), root_folder_name=root.name)
    items = scan_local_folder(root)
    _folders, documents = scan_items(items)
    profiles = build_document_profiles(documents, selection=selection)

    extracted = sum(
        1
        for p in profiles
        if p.extraction_status in (ExtractionStatus.SUCCESS, ExtractionStatus.PARTIAL)
    )
    coverage = extracted / len(profiles) if profiles else 0.0

    candidates: list[CanonDocumentCandidate] = [assign_topic(p) for p in profiles]
    grouped = group_candidates_by_topic(candidates)

    topic_results: list[CanonTopicResult] = []
    for topic_def in CANON_TOPICS:
        topic_candidates = grouped[topic_def.topic_id]
        recommended: str | None = None
        if topic_candidates:
            top = topic_candidates[0]
            recommended = top.file_id
            for cand in topic_candidates:
                cand.recommended_canon = cand.file_id == recommended
                if cand.file_id == recommended:
                    cand.authority_level = AuthorityLevel.CANONICAL
                else:
                    cand.authority_level = AuthorityLevel.APPROVED

        gap = len(topic_candidates) == 0
        topic_results.append(
            CanonTopicResult(
                topic_id=topic_def.topic_id,
                title=topic_def.title,
                description=topic_def.description,
                candidates=topic_candidates,
                recommended_file_id=recommended,
                gap=gap,
                gap_message=(
                    f"No documents matched topic '{topic_def.title}'. "
                    "Consider creating or uploading a canon document."
                    if gap
                    else None
                ),
            )
        )

    unassigned = [c.file_id for c in candidates if c.topic_id == CanonTopicId.UNASSIGNED]
    cross_refs = detect_cross_reference_issues(profiles)
    purpose_issues = detect_purpose_collisions(candidates, profiles)
    all_cross = cross_refs + purpose_issues
    near_dups = detect_near_duplicate_groups(profiles)

    return CanonizationResult(
        corpus_root=str(root),
        canon_folder_relative=canon_folder_relative,
        topics=topic_results,
        cross_reference_issues=all_cross,
        near_duplicate_groups=near_dups,
        unassigned_documents=unassigned,
        extraction_coverage_ratio=round(coverage, 4),
    )
