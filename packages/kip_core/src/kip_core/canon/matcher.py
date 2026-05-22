"""Assign documents to LaunchBuild1 canon topics."""

from __future__ import annotations

from kip_core.canon.models import CanonDocumentCandidate, CanonTopicId
from kip_core.canon.topics import CANON_TOPICS, CanonTopicDefinition
from kip_core.domain.governance import AuthorityLevel
from kip_core.organization.models import DocumentProfile, ExtractionStatus


def _score_topic(profile: DocumentProfile, topic: CanonTopicDefinition) -> tuple[float, list[str]]:
    path_lower = profile.relative_path.lower()
    name_lower = profile.name.lower()
    text_blob = " ".join(
        [
            profile.name,
            " ".join(profile.keywords),
            " ".join(profile.title_tokens),
            " ".join(profile.folder_segments),
        ]
    ).lower()

    score = 0.0
    reasons: list[str] = []

    for kw in topic.path_keywords:
        if kw in path_lower:
            score += 2.5
            reasons.append(f"path:{kw}")

    for kw in topic.name_keywords:
        if kw in name_lower:
            score += 3.0
            reasons.append(f"name:{kw}")

    content_hits = sum(1 for kw in topic.content_keywords if kw in text_blob)
    if content_hits:
        score += min(4.0, content_hits * 1.2)
        reasons.append(f"content:{content_hits}")

    if profile.extraction_status == ExtractionStatus.SUCCESS:
        score += 0.5
    elif profile.extraction_status == ExtractionStatus.PARTIAL:
        score += 0.25

    return score, reasons


def assign_topic(profile: DocumentProfile) -> CanonDocumentCandidate:
    best_topic: CanonTopicDefinition | None = None
    best_score = 0.0
    best_reasons: list[str] = []

    for topic in CANON_TOPICS:
        score, reasons = _score_topic(profile, topic)
        if score > best_score:
            best_score = score
            best_topic = topic
            best_reasons = reasons

    if best_topic is None or best_score < 2.0:
        return CanonDocumentCandidate(
            file_id=profile.file_id,
            name=profile.name,
            relative_path=profile.relative_path,
            topic_id=CanonTopicId.UNASSIGNED,
            match_score=round(best_score, 2),
            match_reasons=best_reasons,
        )

    return CanonDocumentCandidate(
        file_id=profile.file_id,
        name=profile.name,
        relative_path=profile.relative_path,
        topic_id=best_topic.topic_id,
        match_score=round(best_score, 2),
        match_reasons=best_reasons,
        authority_level=AuthorityLevel.DRAFT,
    )


def group_candidates_by_topic(
    candidates: list[CanonDocumentCandidate],
) -> dict[CanonTopicId, list[CanonDocumentCandidate]]:
    grouped: dict[CanonTopicId, list[CanonDocumentCandidate]] = {
        t.topic_id: [] for t in CANON_TOPICS
    }
    for cand in candidates:
        if cand.topic_id == CanonTopicId.UNASSIGNED:
            continue
        grouped[cand.topic_id].append(cand)
    for topic_id in grouped:
        grouped[topic_id].sort(key=lambda c: c.match_score, reverse=True)
    return grouped
