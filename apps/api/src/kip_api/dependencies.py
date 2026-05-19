from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from kip_core.auth.jwt import get_user_id_from_token
from kip_core.db.session import get_async_session
from kip_core.queues.interfaces import QueuePublisher
from kip_core.queues.redis_publisher import InMemoryQueuePublisher, RedisQueuePublisher
from kip_core.repositories.document import DocumentRepository
from kip_core.repositories.permission import PermissionRepository
from kip_core.repositories.user import UserRepository
from kip_core.services.retrieval import RetrievalService
from kip_core.services.sync import SyncService

security = HTTPBearer(auto_error=False)

_queue_publisher: QueuePublisher | None = None


def get_queue_publisher() -> QueuePublisher:
    global _queue_publisher
    if _queue_publisher is None:
        try:
            _queue_publisher = RedisQueuePublisher()
        except Exception:
            _queue_publisher = InMemoryQueuePublisher()
    return _queue_publisher


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_session():
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]
Queue = Annotated[QueuePublisher, Depends(get_queue_publisher)]


def get_user_repo(session: DbSession) -> UserRepository:
    return UserRepository(session)


def get_document_repo(session: DbSession) -> DocumentRepository:
    return DocumentRepository(session)


def get_permission_repo(session: DbSession) -> PermissionRepository:
    return PermissionRepository(session)


def get_retrieval_service(
    permission_repo: Annotated[PermissionRepository, Depends(get_permission_repo)],
) -> RetrievalService:
    return RetrievalService(permission_repo)


def get_sync_service(session: DbSession, queue: Queue) -> SyncService:
    return SyncService(session, queue)


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> str:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        user_id = get_user_id_from_token(credentials.credentials)
        return str(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


CurrentUserId = Annotated[str, Depends(get_current_user_id)]
