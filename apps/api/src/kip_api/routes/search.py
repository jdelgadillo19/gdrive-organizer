from fastapi import APIRouter, Depends

from kip_api.dependencies import CurrentUserId, get_retrieval_service
from kip_api.schemas.search import SearchRequest, SearchResponse, SearchResultItem
from kip_core.services.retrieval import RetrievalCandidate, RetrievalService

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    principal: CurrentUserId,
    retrieval: RetrievalService = Depends(get_retrieval_service),
) -> SearchResponse:
    """
    ACL-safe search. Vector retrieval is wired in Milestone 3; ranking pipeline is active.
    """
    # Placeholder candidates until embedding pipeline populates the index
    candidates: list[RetrievalCandidate] = []

    results = await retrieval.search(principal, body.query, candidates, limit=body.limit)
    return SearchResponse(
        query=body.query,
        results=[
            SearchResultItem(
                document_id=r.document_id,
                chunk_id=r.chunk_id,
                title=r.title,
                snippet=r.snippet,
                final_score=r.final_score,
                authority_level=r.authority_level,
                explanation=r.explanation,
            )
            for r in results
        ],
    )
