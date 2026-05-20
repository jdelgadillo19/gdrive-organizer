"""Semantic document clustering via hybrid embedding + lexical similarity."""

from __future__ import annotations

import uuid
from collections import Counter

from kip_core.organization.embeddings import (
    CorpusSemanticModel,
    average_pairwise_semantic_similarity,
    fit_corpus_embeddings,
)
from kip_core.organization.models import (
    ClusterRelationship,
    DocumentCluster,
    DocumentProfile,
    OperationalRole,
    SimilarityBreakdown,
)
from kip_core.organization.semantic_features import profiles_share_operational_role

# Hybrid weights — semantic primary, lexical secondary, context tertiary
_W_SEMANTIC = 0.52
_W_LEXICAL = 0.23
_W_CONTEXT = 0.20
_W_FOLDER_BONUS = 0.05
_DEFAULT_THRESHOLD = 0.32


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _context_similarity(a: DocumentProfile, b: DocumentProfile) -> float:
    ctx_a = set(a.context_tokens) | set(a.temporal_tokens) | set(a.folder_segments)
    ctx_b = set(b.context_tokens) | set(b.temporal_tokens) | set(b.folder_segments)
    role_match = 1.0 if profiles_share_operational_role(a, b) else 0.0
    path_score = _jaccard(ctx_a, ctx_b)
    return round(0.6 * path_score + 0.4 * role_match, 4)


def _folder_bonus(a: DocumentProfile, b: DocumentProfile) -> float:
    if (
        a.folder_segments
        and b.folder_segments
        and a.folder_segments[0] == b.folder_segments[0]
    ):
        return _W_FOLDER_BONUS
    return 0.0


def pairwise_similarity(
    a: DocumentProfile,
    b: DocumentProfile,
    *,
    model: CorpusSemanticModel,
) -> SimilarityBreakdown:
    lexical_a = set(a.keywords) | set(a.title_tokens)
    lexical_b = set(b.keywords) | set(b.title_tokens)
    lexical = _jaccard(lexical_a, lexical_b)
    semantic = model.similarity(a.file_id, b.file_id)
    context = _context_similarity(a, b)
    folder_bonus = _folder_bonus(a, b)
    combined = min(
        1.0,
        _W_SEMANTIC * semantic + _W_LEXICAL * lexical + _W_CONTEXT * context + folder_bonus,
    )
    return SimilarityBreakdown(
        semantic_score=round(semantic, 4),
        lexical_score=round(lexical, 4),
        context_score=round(context, 4),
        folder_bonus=round(folder_bonus, 4),
        combined_score=round(combined, 4),
    )


def pairwise_similarity_debug(
    a: DocumentProfile,
    b: DocumentProfile,
    *,
    model: CorpusSemanticModel | None = None,
) -> dict[str, float | str]:
    fitted = model or fit_corpus_embeddings([a, b])
    breakdown = pairwise_similarity(a, b, model=fitted)
    return {
        "embedder": fitted.embedder_name,
        **breakdown.model_dump(),
        "operational_role_a": a.operational_role.value,
        "operational_role_b": b.operational_role.value,
        "shared_operational_role": profiles_share_operational_role(a, b),
    }


def _infer_relationship(
    members: list[DocumentProfile],
    *,
    avg_semantic: float,
    avg_lexical: float,
) -> ClusterRelationship:
    roles = {m.operational_role for m in members}
    if len(roles) == 1 and OperationalRole.UNKNOWN not in roles:
        sole = next(iter(roles))
        if sole not in {OperationalRole.GENERAL, OperationalRole.UNKNOWN}:
            return ClusterRelationship.SHARED_OPERATIONAL_ROLE
    if avg_semantic >= 0.45 and avg_lexical < 0.35:
        return ClusterRelationship.SHARED_SEMANTIC_TOPIC
    if avg_lexical >= 0.4 and avg_semantic < 0.35:
        return ClusterRelationship.SHARED_TERMINOLOGY
    return ClusterRelationship.MIXED_SIGNALS


def _shared_and_distinguishing_signals(
    members: list[DocumentProfile],
) -> tuple[list[str], list[str]]:
    keyword_sets = [set(m.keywords) for m in members]
    if not keyword_sets:
        return [], []
    shared = set.intersection(*keyword_sets) if len(keyword_sets) > 1 else keyword_sets[0]
    union = set.union(*keyword_sets)
    distinguishing = union - shared
    def _kw_weight(k: str) -> int:
        return sum(1 for ks in keyword_sets if k in ks)

    shared_list = sorted(shared, key=_kw_weight, reverse=True)[:6]
    dist_list = sorted(distinguishing)[:4]
    role_label = members[0].operational_role.value
    if role_label not in ("unknown", "general"):
        shared_list = [f"role:{role_label}", *shared_list]
    return shared_list, dist_list


def _cluster_label(
    keywords: list[str],
    title_samples: list[str],
    operational_role: OperationalRole,
) -> str:
    if operational_role not in {OperationalRole.UNKNOWN, OperationalRole.GENERAL}:
        role_title = operational_role.value.replace("_", " ").title()
        if keywords:
            return f"{role_title} — {keywords[0].title()}"
        return role_title
    if keywords:
        return " / ".join(keywords[:3]).title()
    if title_samples:
        return title_samples[0].rsplit(".", 1)[0].replace("_", " ").title()
    return "Miscellaneous Documents"


def cluster_documents(
    profiles: list[DocumentProfile],
    *,
    similarity_threshold: float = _DEFAULT_THRESHOLD,
) -> list[DocumentCluster]:
    """
    Greedy clustering on hybrid semantic (TF-IDF / optional ST) + lexical + context.

    Threshold is conservative to avoid over-merging unrelated files.
    """
    if not profiles:
        return []

    model = fit_corpus_embeddings(profiles)
    unassigned = list(profiles)
    clusters: list[DocumentCluster] = []

    while unassigned:
        seed = unassigned.pop(0)
        members = [seed]
        remaining: list[DocumentProfile] = []

        for candidate in unassigned:
            breakdown = pairwise_similarity(seed, candidate, model=model)
            if breakdown.combined_score >= similarity_threshold:
                members.append(candidate)
            else:
                remaining.append(candidate)

        unassigned = remaining
        all_keywords: list[str] = []
        for member in members:
            all_keywords.extend(member.keywords)
        keyword_counts: Counter[str] = Counter(all_keywords)
        top_keywords = [kw for kw, _ in keyword_counts.most_common(6)]

        file_ids = [m.file_id for m in members]
        if len(members) == 1:
            cohesion = 1.0
            breakdown = SimilarityBreakdown(combined_score=1.0)
        else:
            pairwise_scores: list[SimilarityBreakdown] = []
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    pairwise_scores.append(
                        pairwise_similarity(members[i], members[j], model=model)
                    )
            cohesion = (
                sum(p.combined_score for p in pairwise_scores) / len(pairwise_scores)
                if pairwise_scores
                else 0.5
            )
            breakdown = SimilarityBreakdown(
                semantic_score=round(
                    sum(p.semantic_score for p in pairwise_scores) / len(pairwise_scores), 4
                ),
                lexical_score=round(
                    sum(p.lexical_score for p in pairwise_scores) / len(pairwise_scores), 4
                ),
                context_score=round(
                    sum(p.context_score for p in pairwise_scores) / len(pairwise_scores), 4
                ),
                combined_score=round(cohesion, 4),
            )

        avg_sem = breakdown.semantic_score
        avg_lex = breakdown.lexical_score
        relationship = _infer_relationship(members, avg_semantic=avg_sem, avg_lexical=avg_lex)
        shared_signals, distinguishing = _shared_and_distinguishing_signals(members)
        dominant_role = members[0].operational_role
        if len({m.operational_role for m in members}) == 1:
            dominant_role = members[0].operational_role

        semantic_cohesion = average_pairwise_semantic_similarity(model, file_ids)
        label = _cluster_label(top_keywords, [m.name for m in members], dominant_role)

        signal_summary = ", ".join(shared_signals[:4]) or "contextual document similarity"
        rationale = (
            f"Grouped {len(members)} document(s) via {relationship.value.replace('_', ' ')} "
            f"(semantic cohesion {semantic_cohesion:.2f}): {signal_summary}."
        )

        clusters.append(
            DocumentCluster(
                cluster_id=str(uuid.uuid4()),
                label=label,
                member_file_ids=file_ids,
                top_keywords=top_keywords,
                cohesion_score=round(min(1.0, cohesion), 4),
                rationale=rationale,
                relationship_type=relationship,
                operational_role=dominant_role,
                similarity_breakdown=breakdown,
                shared_signals=shared_signals,
                distinguishing_signals=distinguishing,
            )
        )

    return clusters
