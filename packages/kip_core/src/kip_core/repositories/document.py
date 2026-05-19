import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from kip_core.db.models.document import Document, DocumentGovernance
from kip_core.repositories.base import BaseRepository


class DocumentRepository(BaseRepository):
    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        result = await self._session.execute(
            select(Document)
            .where(Document.id == document_id)
            .options(
                selectinload(Document.governance),
                selectinload(Document.permissions),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_connection(
        self,
        connection_id: uuid.UUID,
        *,
        limit: int = 100,
    ) -> list[Document]:
        result = await self._session.execute(
            select(Document)
            .where(Document.connection_id == connection_id)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def upsert_governance(
        self,
        document_id: uuid.UUID,
        *,
        authority_level: str,
        lifecycle_status: str,
        freshness_score: float,
        trust_score: float,
    ) -> DocumentGovernance:
        doc = await self.get_by_id(document_id)
        if doc is None:
            raise ValueError(f"Document {document_id} not found")
        if doc.governance is None:
            gov = DocumentGovernance(
                document_id=document_id,
                authority_level=authority_level,
                lifecycle_status=lifecycle_status,
                freshness_score=freshness_score,
                trust_score=trust_score,
            )
            self._session.add(gov)
        else:
            doc.governance.authority_level = authority_level
            doc.governance.lifecycle_status = lifecycle_status
            doc.governance.freshness_score = freshness_score
            doc.governance.trust_score = trust_score
            gov = doc.governance
        await self._session.flush()
        return gov
