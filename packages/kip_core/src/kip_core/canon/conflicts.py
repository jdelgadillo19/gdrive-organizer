"""Cross-reference reconciliation and near-duplicate detection."""

from __future__ import annotations

import re

from kip_core.canon.models import (
    CanonDocumentCandidate,
    ConflictSeverity,
    CrossReferenceIssue,
    CrossReferenceKind,
)
from kip_core.canon.topics import CROSS_REFERENCE_PAIRS
from kip_core.organization.clustering import pairwise_similarity
from kip_core.organization.embeddings import fit_corpus_embeddings
from kip_core.organization.models import DocumentProfile

_CONFLICT_TOKEN_PAIRS: tuple[tuple[str, str], ...] = (
    ("saturday", "sunday"),
    ("am service", "pm service"),
    ("must not", "must"),
)


def _profile_text(profile: DocumentProfile) -> str:
    parts = [profile.name]
    if profile.extracted_text:
        parts.append(profile.extracted_text[:4000])
    return "\n".join(parts).lower()


def _contradiction_signals(text_a: str, text_b: str) -> list[str]:
    signals: list[str] = []
    for left, right in _CONFLICT_TOKEN_PAIRS:
        if (left in text_a and right in text_b) or (right in text_a and left in text_b):
            signals.append(f"opposing_terms:{left}/{right}")
    nums_a = set(re.findall(r"\b\d{1,2}:\d{2}\b", text_a))
    nums_b = set(re.findall(r"\b\d{1,2}:\d{2}\b", text_b))
    if nums_a and nums_b and not nums_a & nums_b:
        signals.append(f"time_mismatch:{sorted(nums_a)[:3]} vs {sorted(nums_b)[:3]}")
    return signals


def _find_profile(profiles: list[DocumentProfile], fragment: str) -> DocumentProfile | None:
    frag = fragment.lower()
    for profile in profiles:
        if frag in profile.relative_path.lower() or frag in profile.name.lower():
            return profile
    return None


def detect_cross_reference_issues(profiles: list[DocumentProfile]) -> list[CrossReferenceIssue]:
    model = fit_corpus_embeddings(profiles)
    issues: list[CrossReferenceIssue] = []

    for pair in CROSS_REFERENCE_PAIRS:
        pa = _find_profile(profiles, pair.path_a_contains)
        pb = _find_profile(profiles, pair.path_b_contains)
        if pa is None or pb is None:
            continue
        breakdown = pairwise_similarity(pa, pb, model=model)
        text_a = _profile_text(pa)
        text_b = _profile_text(pb)
        signals = _contradiction_signals(text_a, text_b)
        sim = breakdown.combined_score

        if sim >= 0.88:
            kind = CrossReferenceKind.NEAR_DUPLICATE
            severity = ConflictSeverity.HIGH
            summary = (
                f"{pair.label}: near-duplicate (similarity={sim:.2f}). "
                "Pick one canon or merge intentionally."
            )
        elif signals:
            kind = CrossReferenceKind.SAME_TOPIC_RECONCILE
            severity = ConflictSeverity.HIGH
            summary = (
                f"{pair.label}: related documents with possible contradictions "
                f"(similarity={sim:.2f})."
            )
        elif 0.35 <= sim < 0.88:
            kind = CrossReferenceKind.SAME_TOPIC_RECONCILE
            severity = ConflictSeverity.MEDIUM
            summary = (
                f"{pair.label}: cross-reference review recommended (similarity={sim:.2f})."
            )
        else:
            continue

        issues.append(
            CrossReferenceIssue(
                kind=kind,
                file_a=pa.file_id,
                file_b=pb.file_id,
                title_a=pa.name,
                title_b=pb.name,
                similarity=sim,
                severity=severity,
                summary=summary,
                contradiction_signals=signals,
            )
        )

    return issues


def detect_near_duplicate_groups(
    profiles: list[DocumentProfile],
    *,
    threshold: float = 0.88,
) -> list[list[str]]:
    model = fit_corpus_embeddings(profiles)
    groups: list[list[str]] = []
    used: set[str] = set()

    for i, pa in enumerate(profiles):
        if pa.file_id in used:
            continue
        cluster = [pa.file_id]
        for pb in profiles[i + 1 :]:
            if pb.file_id in used:
                continue
            sim = pairwise_similarity(pa, pb, model=model).combined_score
            if sim >= threshold:
                cluster.append(pb.file_id)
        if len(cluster) > 1:
            for fid in cluster:
                used.add(fid)
            groups.append(cluster)

    return groups


def detect_purpose_collisions(
    candidates: list[CanonDocumentCandidate],
    profiles: list[DocumentProfile],
    *,
    threshold: float = 0.82,
) -> list[CrossReferenceIssue]:
    """Same topic assignment with high similarity — likely duplicate purpose."""
    if not candidates:
        return []

    by_topic: dict[str, list[CanonDocumentCandidate]] = {}
    for cand in candidates:
        if cand.topic_id.value == "unassigned":
            continue
        by_topic.setdefault(cand.topic_id.value, []).append(cand)

    profile_by_id = {p.file_id: p for p in profiles}
    model = fit_corpus_embeddings(profiles)
    issues: list[CrossReferenceIssue] = []

    for topic_key, group in by_topic.items():
        if len(group) < 2:
            continue
        for i, ca in enumerate(group):
            pa = profile_by_id.get(ca.file_id)
            if pa is None:
                continue
            for cb in group[i + 1 :]:
                pb = profile_by_id.get(cb.file_id)
                if pb is None:
                    continue
                sim = pairwise_similarity(pa, pb, model=model).combined_score
                if sim < threshold:
                    continue
                issues.append(
                    CrossReferenceIssue(
                        kind=CrossReferenceKind.PURPOSE_COLLISION,
                        file_a=pa.file_id,
                        file_b=pb.file_id,
                        title_a=pa.name,
                        title_b=pb.name,
                        similarity=sim,
                        severity=ConflictSeverity.HIGH,
                        summary=(
                            f"Topic '{topic_key}': two documents may serve the same purpose "
                            f"(similarity={sim:.2f}). Designate one canon or split scopes."
                        ),
                    )
                )
    return issues
