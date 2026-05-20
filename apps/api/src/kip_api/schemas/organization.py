from datetime import datetime
from typing import Any

from kip_core.organization.models import (
    AnalysisPreferences,
    ConfidenceLevel,
    FolderSelection,
    RecommendationType,
    ScannedDriveItem,
)
from pydantic import BaseModel, Field


class OrganizationAnalyzeRequest(BaseModel):
    selection: FolderSelection
    items: list[ScannedDriveItem] = Field(min_length=1)
    preferences: AnalysisPreferences | None = None


class RollbackMetadataResponse(BaseModel):
    snapshot_id: str
    operation_type: str
    file_id: str
    original_path: str
    original_name: str
    proposed_path: str | None
    proposed_name: str | None
    parent_folder_id: str | None
    recorded_at: datetime
    reversible: bool
    execution_deferred: bool


class RecommendationResponse(BaseModel):
    id: str
    recommendation_type: RecommendationType
    title: str
    rationale: str
    detailed_explanation: str
    confidence_score: float
    confidence_level: ConfidenceLevel
    impacted_file_ids: list[str]
    proposed_destination_path: str | None
    proposed_name: str | None
    cluster_id: str | None
    rollback: RollbackMetadataResponse
    requires_approval: bool
    auto_apply_allowed: bool
    metadata: dict[str, Any]


class OrganizationAnalyzeResponse(BaseModel):
    analysis_id: str
    selection: FolderSelection
    preferences: AnalysisPreferences
    scanned_item_count: int
    document_count: int
    extraction_summary: dict[str, int]
    coherence_score: float
    is_well_organized: bool
    cluster_count: int
    recommendations: list[RecommendationResponse]
    generated_at: datetime
