from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    limit: int = Field(default=20, ge=1, le=100)


class SearchResultItem(BaseModel):
    document_id: str
    chunk_id: str | None
    title: str
    snippet: str
    final_score: float
    authority_level: str
    explanation: dict[str, float]


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
