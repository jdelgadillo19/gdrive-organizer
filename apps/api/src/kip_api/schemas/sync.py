from pydantic import BaseModel
from uuid import UUID


class SyncStartRequest(BaseModel):
    connection_id: UUID
    watched_folder_id: UUID | None = None


class SyncStatusResponse(BaseModel):
    job_id: UUID
    status: str
    error_message: str | None = None
