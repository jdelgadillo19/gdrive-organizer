from uuid import UUID

from fastapi import APIRouter, HTTPException

from kip_api.dependencies import CurrentUserId, DbSession, Queue
from kip_api.schemas.sync import SyncStartRequest, SyncStatusResponse
from kip_core.services.sync import SyncService

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/start", response_model=SyncStatusResponse)
async def sync_start(
    body: SyncStartRequest,
    db: DbSession,
    queue: Queue,
    _user: CurrentUserId,
) -> SyncStatusResponse:
    service = SyncService(db, queue)
    job = await service.start_sync(body.connection_id, body.watched_folder_id)
    await db.commit()
    return SyncStatusResponse(job_id=job.id, status=job.status)


@router.get("/status", response_model=SyncStatusResponse)
async def sync_status(
    job_id: UUID,
    db: DbSession,
    queue: Queue,
    _user: CurrentUserId,
) -> SyncStatusResponse:
    service = SyncService(db, queue)
    job = await service.get_status(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Sync job not found")
    return SyncStatusResponse(job_id=job.id, status=job.status, error_message=job.error_message)
