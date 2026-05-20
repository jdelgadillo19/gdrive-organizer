from fastapi import APIRouter
from kip_core.services.organization import OrganizationService

from kip_api.dependencies import CurrentUserId
from kip_api.schemas.organization import (
    OrganizationAnalyzeRequest,
    OrganizationAnalyzeResponse,
    RecommendationResponse,
    RollbackMetadataResponse,
)

router = APIRouter(prefix="/organization", tags=["organization"])


@router.post("/analyze", response_model=OrganizationAnalyzeResponse)
async def analyze_organization(
    body: OrganizationAnalyzeRequest,
    _user: CurrentUserId,
) -> OrganizationAnalyzeResponse:
    """
    Generate organizational recommendations for a scanned Drive folder.

    Does not modify any files — recommendations require explicit user approval.
    """
    service = OrganizationService()
    result = service.analyze_folder(body.selection, body.items, body.preferences)

    return OrganizationAnalyzeResponse(
        analysis_id=result.analysis_id,
        selection=result.selection,
        preferences=result.preferences,
        scanned_item_count=result.scanned_item_count,
        document_count=result.document_count,
        extraction_summary=result.extraction_summary,
        coherence_score=result.structure_assessment.coherence_score,
        is_well_organized=result.structure_assessment.is_well_organized,
        cluster_count=len(result.clusters),
        recommendations=[
            RecommendationResponse(
                id=r.id,
                recommendation_type=r.recommendation_type,
                title=r.title,
                rationale=r.rationale,
                detailed_explanation=r.detailed_explanation,
                confidence_score=r.confidence_score,
                confidence_level=r.confidence_level,
                impacted_file_ids=r.impacted_file_ids,
                proposed_destination_path=r.proposed_destination_path,
                proposed_name=r.proposed_name,
                cluster_id=r.cluster_id,
                rollback=RollbackMetadataResponse(
                    snapshot_id=r.rollback.snapshot_id,
                    operation_type=r.rollback.operation_type,
                    file_id=r.rollback.file_id,
                    original_path=r.rollback.original_path,
                    original_name=r.rollback.original_name,
                    proposed_path=r.rollback.proposed_path,
                    proposed_name=r.rollback.proposed_name,
                    parent_folder_id=r.rollback.parent_folder_id,
                    recorded_at=r.rollback.recorded_at,
                    reversible=r.rollback.reversible,
                    execution_deferred=r.rollback.execution_deferred,
                ),
                requires_approval=r.requires_approval,
                auto_apply_allowed=r.auto_apply_allowed,
                metadata=r.metadata,
            )
            for r in result.recommendations
        ],
        generated_at=result.generated_at,
    )
