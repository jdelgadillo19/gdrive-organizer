"""ACL-safe semantic retrieval — ACL filtering always precedes ranking."""

from dataclasses import dataclass
from uuid import UUID

from kip_core.domain.governance import AuthorityLevel, LifecycleStatus, is_retrieval_eligible
from kip_core.domain.ranking import RankingSignals, RankedCandidate, rank_candidates
from kip_core.repositories.permission import PermissionRepository


@dataclass(frozen=True)
class RetrievalCandidate:
    document_id: UUID
    chunk_id: UUID | None
    title: str
    snippet: str
    semantic_score: float
    authority_level: AuthorityLevel
    lifecycle_status: LifecycleStatus
    freshness_score: float


@dataclass(frozen=True)
class SearchResult:
    document_id: str
    chunk_id: str | None
    title: str
    snippet: str
    final_score: float
    authority_level: str
    explanation: dict[str, float]


class RetrievalService:
    def __init__(self, permission_repo: PermissionRepository) -> None:
        self._permission_repo = permission_repo

    async def search(
        self,
        principal: str,
        query: str,
        candidates: list[RetrievalCandidate],
        *,
        limit: int = 20,
    ) -> list[SearchResult]:
        """
        Pipeline:
        1. ACL filter (permission repository)
        2. Governance eligibility filter
        3. Composite ranking (never semantic-only)
        """
        _ = query  # embedding query wired in Milestone 3
        allowed_ids = await self._permission_repo.get_accessible_document_ids(principal)

        acl_filtered: list[RetrievalCandidate] = [
            c for c in candidates if c.document_id in allowed_ids
        ]

        eligible: list[RetrievalCandidate] = [
            c
            for c in acl_filtered
            if is_retrieval_eligible(c.authority_level, c.lifecycle_status)
        ]

        ranking_input: list[tuple[str, str | None, RankingSignals]] = [
            (
                str(c.document_id),
                str(c.chunk_id) if c.chunk_id else None,
                RankingSignals(
                    semantic_score=c.semantic_score,
                    authority_level=c.authority_level,
                    freshness_score=c.freshness_score,
                ),
            )
            for c in eligible
        ]

        ranked: list[RankedCandidate] = rank_candidates(ranking_input)

        results: list[SearchResult] = []
        candidate_by_id = {str(c.document_id): c for c in eligible}
        for r in ranked[:limit]:
            src = candidate_by_id.get(r.document_id)
            if src is None:
                continue
            results.append(
                SearchResult(
                    document_id=r.document_id,
                    chunk_id=r.chunk_id,
                    title=src.title,
                    snippet=src.snippet,
                    final_score=r.final_score,
                    authority_level=src.authority_level.value,
                    explanation=r.explanation,
                )
            )
        return results
