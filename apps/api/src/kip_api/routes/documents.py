from uuid import UUID

from fastapi import APIRouter, HTTPException

from kip_api.dependencies import CurrentUserId, get_document_repo, get_permission_repo
from kip_core.repositories.document import DocumentRepository
from kip_core.repositories.permission import PermissionRepository
from fastapi import Depends

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    principal: CurrentUserId,
    doc_repo: DocumentRepository = Depends(get_document_repo),
    perm_repo: PermissionRepository = Depends(get_permission_repo),
) -> dict:
    if not await perm_repo.principal_can_read(principal, document_id):
        raise HTTPException(status_code=403, detail="Access denied")

    doc = await doc_repo.get_by_id(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    governance = None
    if doc.governance:
        governance = {
            "authority_level": doc.governance.authority_level,
            "lifecycle_status": doc.governance.lifecycle_status,
            "trust_score": doc.governance.trust_score,
            "freshness_score": doc.governance.freshness_score,
            "reviewed_at": doc.governance.reviewed_at,
            "reviewed_by": doc.governance.reviewed_by,
        }

    return {
        "id": str(doc.id),
        "source_id": doc.source_id,
        "title": doc.title,
        "mime_type": doc.mime_type,
        "owner": doc.owner,
        "department": doc.department,
        "processing_status": doc.processing_status,
        "governance": governance,
    }
