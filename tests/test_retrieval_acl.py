import uuid
from unittest.mock import AsyncMock

import pytest

from kip_core.domain.governance import AuthorityLevel, LifecycleStatus
from kip_core.repositories.permission import PermissionRepository
from kip_core.services.retrieval import RetrievalCandidate, RetrievalService


@pytest.mark.asyncio
async def test_acl_filters_before_ranking() -> None:
    allowed_id = uuid.uuid4()
    denied_id = uuid.uuid4()

    perm_repo = AsyncMock(spec=PermissionRepository)
    perm_repo.get_accessible_document_ids = AsyncMock(return_value={allowed_id})

    service = RetrievalService(perm_repo)
    candidates = [
        RetrievalCandidate(
            document_id=allowed_id,
            chunk_id=None,
            title="Allowed",
            snippet="snippet",
            semantic_score=0.5,
            authority_level=AuthorityLevel.APPROVED,
            lifecycle_status=LifecycleStatus.ACTIVE,
            freshness_score=1.0,
        ),
        RetrievalCandidate(
            document_id=denied_id,
            chunk_id=None,
            title="Denied",
            snippet="snippet",
            semantic_score=0.99,
            authority_level=AuthorityLevel.CANONICAL,
            lifecycle_status=LifecycleStatus.ACTIVE,
            freshness_score=1.0,
        ),
    ]

    results = await service.search("user@example.com", "query", candidates, limit=10)
    assert len(results) == 1
    assert results[0].document_id == str(allowed_id)
