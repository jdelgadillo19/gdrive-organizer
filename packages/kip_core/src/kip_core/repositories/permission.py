import uuid

from sqlalchemy import select

from kip_core.db.models.permission import PermissionMapping
from kip_core.repositories.base import BaseRepository


class PermissionRepository(BaseRepository):
    async def get_accessible_document_ids(
        self,
        principal: str,
        *,
        min_level: str = "read",
    ) -> set[uuid.UUID]:
        """Return document IDs the principal may read. ACL filter runs before ranking."""
        levels = _levels_at_or_above(min_level)
        result = await self._session.execute(
            select(PermissionMapping.document_id).where(
                PermissionMapping.principal == principal,
                PermissionMapping.permission_level.in_(levels),
            )
        )
        return {row[0] for row in result.all()}

    async def principal_can_read(self, principal: str, document_id: uuid.UUID) -> bool:
        allowed = await self.get_accessible_document_ids(principal, min_level="read")
        return document_id in allowed


def _levels_at_or_above(min_level: str) -> list[str]:
    order = ["read", "comment", "write", "owner"]
    if min_level not in order:
        return ["read", "comment", "write", "owner"]
    idx = order.index(min_level)
    return order[idx:]
