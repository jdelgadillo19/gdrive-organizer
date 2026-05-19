"""Incremental Drive sync orchestration (foundation)."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from kip_core.db.models.sync import SyncJob
from kip_core.logging import get_logger
from kip_core.queues.interfaces import QueuePublisher, SyncJobMessage

logger = get_logger(__name__)


class SyncService:
    def __init__(self, session: AsyncSession, queue: QueuePublisher) -> None:
        self._session = session
        self._queue = queue

    async def start_sync(self, connection_id: UUID, watched_folder_id: UUID | None = None) -> SyncJob:
        job = SyncJob(connection_id=connection_id, status="pending", started_at=datetime.now(UTC))
        self._session.add(job)
        await self._session.flush()

        idempotency_key = f"sync:{connection_id}:{watched_folder_id or 'all'}"
        queue_job_id = await self._queue.enqueue_sync(
            SyncJobMessage(
                connection_id=connection_id,
                watched_folder_id=watched_folder_id,
                idempotency_key=idempotency_key,
                enqueued_at=datetime.now(UTC),
            )
        )
        logger.info(
            "sync_job_enqueued",
            sync_job_id=str(job.id),
            queue_job_id=queue_job_id,
            connection_id=str(connection_id),
        )
        return job

    async def get_status(self, job_id: UUID) -> SyncJob | None:
        return await self._session.get(SyncJob, job_id)
