"""Queue interfaces — implementations swap (in-memory, Redis, Celery) without changing callers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class SyncJobMessage:
    connection_id: UUID
    watched_folder_id: UUID | None
    idempotency_key: str
    enqueued_at: datetime


@dataclass(frozen=True)
class ProcessingJob:
    document_id: UUID
    source_id: str
    checksum: str
    idempotency_key: str


@dataclass(frozen=True)
class EmbeddingJob:
    chunk_id: UUID
    document_id: UUID
    idempotency_key: str


class QueuePublisher(ABC):
    @abstractmethod
    async def enqueue_sync(self, message: SyncJobMessage) -> str:
        """Return job id."""

    @abstractmethod
    async def enqueue_processing(self, job: ProcessingJob) -> str:
        """Return job id."""

    @abstractmethod
    async def enqueue_embedding(self, job: EmbeddingJob) -> str:
        """Return job id."""
