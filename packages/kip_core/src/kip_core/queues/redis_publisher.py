import json
from datetime import UTC, datetime
from uuid import uuid4

import redis.asyncio as redis

from kip_core.config import get_settings
from kip_core.queues.interfaces import EmbeddingJob, ProcessingJob, QueuePublisher, SyncJobMessage

QUEUES = {
    "sync": "kip:queue:sync",
    "processing": "kip:queue:processing",
    "embedding": "kip:queue:embedding",
}


class RedisQueuePublisher(QueuePublisher):
    def __init__(self, client: redis.Redis | None = None) -> None:
        settings = get_settings()
        self._client = client or redis.from_url(settings.redis_url, decode_responses=True)

    async def enqueue_sync(self, message: SyncJobMessage) -> str:
        job_id = str(uuid4())
        payload = {
            "job_id": job_id,
            "connection_id": str(message.connection_id),
            "watched_folder_id": str(message.watched_folder_id) if message.watched_folder_id else None,
            "idempotency_key": message.idempotency_key,
            "enqueued_at": message.enqueued_at.isoformat(),
        }
        await self._client.lpush(QUEUES["sync"], json.dumps(payload))
        return job_id

    async def enqueue_processing(self, job: ProcessingJob) -> str:
        job_id = str(uuid4())
        payload = {
            "job_id": job_id,
            "document_id": str(job.document_id),
            "source_id": job.source_id,
            "checksum": job.checksum,
            "idempotency_key": job.idempotency_key,
        }
        await self._client.lpush(QUEUES["processing"], json.dumps(payload))
        return job_id

    async def enqueue_embedding(self, job: EmbeddingJob) -> str:
        job_id = str(uuid4())
        payload = {
            "job_id": job_id,
            "chunk_id": str(job.chunk_id),
            "document_id": str(job.document_id),
            "idempotency_key": job.idempotency_key,
        }
        await self._client.lpush(QUEUES["embedding"], json.dumps(payload))
        return job_id


class InMemoryQueuePublisher(QueuePublisher):
    """Deterministic in-memory queue for tests and local dev without Redis."""

    def __init__(self) -> None:
        self.sync_jobs: list[SyncJobMessage] = []
        self.processing_jobs: list[ProcessingJob] = []
        self.embedding_jobs: list[EmbeddingJob] = []

    async def enqueue_sync(self, message: SyncJobMessage) -> str:
        self.sync_jobs.append(message)
        return str(uuid4())

    async def enqueue_processing(self, job: ProcessingJob) -> str:
        self.processing_jobs.append(job)
        return str(uuid4())

    async def enqueue_embedding(self, job: EmbeddingJob) -> str:
        self.embedding_jobs.append(job)
        return str(uuid4())
