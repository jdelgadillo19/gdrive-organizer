"""Explainable composite ranking — semantic similarity never alone determines order."""

from dataclasses import dataclass

from kip_core.domain.governance import AuthorityLevel, authority_weight


@dataclass(frozen=True)
class RankingSignals:
    semantic_score: float
    authority_level: AuthorityLevel
    freshness_score: float
    usage_score: float = 0.0
    metadata_quality_score: float = 1.0


@dataclass(frozen=True)
class RankedCandidate:
    document_id: str
    chunk_id: str | None
    final_score: float
    semantic_score: float
    authority_score: float
    freshness_score: float
    explanation: dict[str, float]


# Weights from docs/planning/23-ranking-and-scoring.md
WEIGHT_SEMANTIC = 0.45
WEIGHT_AUTHORITY = 0.25
WEIGHT_FRESHNESS = 0.15
WEIGHT_USAGE = 0.10
WEIGHT_METADATA = 0.05


def composite_score(signals: RankingSignals) -> float:
    authority = authority_weight(signals.authority_level)
    return (
        signals.semantic_score * WEIGHT_SEMANTIC
        + authority * WEIGHT_AUTHORITY
        + signals.freshness_score * WEIGHT_FRESHNESS
        + signals.usage_score * WEIGHT_USAGE
        + signals.metadata_quality_score * WEIGHT_METADATA
    )


def rank_candidates(
    candidates: list[tuple[str, str | None, RankingSignals]],
) -> list[RankedCandidate]:
    """Rank pre-ACL-filtered candidates. Caller must filter ACL first."""
    ranked: list[RankedCandidate] = []
    for document_id, chunk_id, signals in candidates:
        authority = authority_weight(signals.authority_level)
        final = composite_score(signals)
        ranked.append(
            RankedCandidate(
                document_id=document_id,
                chunk_id=chunk_id,
                final_score=final,
                semantic_score=signals.semantic_score,
                authority_score=authority,
                freshness_score=signals.freshness_score,
                explanation={
                    "semantic": round(signals.semantic_score * WEIGHT_SEMANTIC, 4),
                    "authority": round(authority * WEIGHT_AUTHORITY, 4),
                    "freshness": round(signals.freshness_score * WEIGHT_FRESHNESS, 4),
                    "usage": round(signals.usage_score * WEIGHT_USAGE, 4),
                    "metadata_quality": round(
                        signals.metadata_quality_score * WEIGHT_METADATA, 4
                    ),
                },
            )
        )
    ranked.sort(key=lambda r: r.final_score, reverse=True)
    return ranked
