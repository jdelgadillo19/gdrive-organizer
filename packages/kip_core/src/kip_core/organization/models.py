"""Structured recommendation objects for organizational intelligence."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class RecommendationType(StrEnum):
    FOLDER_CREATE = "folder_create"
    FILE_MOVE = "file_move"
    FILE_RENAME = "file_rename"
    PRESERVE_STRUCTURE = "preserve_structure"
    INFORMATIONAL = "informational"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExtractionStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    FAILED = "failed"


class DriveMimeType(StrEnum):
    PDF = "application/pdf"
    GOOGLE_DOC = "application/vnd.google-apps.document"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    GOOGLE_SHEET = "application/vnd.google-apps.spreadsheet"
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    PLAIN_TEXT = "text/plain"
    FOLDER = "application/vnd.google-apps.folder"


SUPPORTED_CONTENT_MIMES: frozenset[str] = frozenset(
    {
        DriveMimeType.PDF,
        DriveMimeType.GOOGLE_DOC,
        DriveMimeType.DOCX,
        DriveMimeType.GOOGLE_SHEET,
        DriveMimeType.XLSX,
        DriveMimeType.PPTX,
        DriveMimeType.PLAIN_TEXT,
    }
)


class OperationalRole(StrEnum):
    """High-level document role inferred from content and path signals."""

    FINANCIAL = "financial"
    LEGAL = "legal"
    OPERATIONS = "operations"
    PLANNING = "planning"
    REPORTING = "reporting"
    GENERAL = "general"
    UNKNOWN = "unknown"


class ClusterRelationship(StrEnum):
    """Why cluster members were grouped — aids explainability."""

    SHARED_OPERATIONAL_ROLE = "shared_operational_role"
    SHARED_SEMANTIC_TOPIC = "shared_semantic_topic"
    SHARED_TERMINOLOGY = "shared_terminology"
    MIXED_SIGNALS = "mixed_signals"


class FolderSelection(BaseModel):
    """User-selected organizational scope within a Drive repository."""

    root_folder_id: str
    root_folder_name: str
    scope_label: str | None = None


class AnalysisPreferences(BaseModel):
    """Optional tuning for conservative organizational analysis."""

    max_proposed_depth: int = Field(default=3, ge=1, le=6)
    prefer_minimal_changes: bool = True
    preserve_existing_coherent_folders: bool = True
    enable_rename_recommendations: bool = True
    enable_relocation_recommendations: bool = True
    min_cluster_size_for_relocation: int = Field(default=2, ge=2, le=10)
    min_relocation_cohesion: float = Field(default=0.38, ge=0.0, le=1.0)
    min_usefulness_score: float = Field(default=0.42, ge=0.0, le=1.0)
    max_relocation_recommendations: int = Field(default=12, ge=1, le=50)
    max_rename_recommendations: int = Field(default=8, ge=1, le=50)


class ScannedDriveItem(BaseModel):
    """A file or folder discovered during recursive scan (pre- or post-extraction)."""

    file_id: str
    name: str
    mime_type: str
    parent_folder_id: str | None = None
    relative_path: str = ""
    is_folder: bool = False
    size_bytes: int | None = None
    modified_at: datetime | None = None
    raw_content: bytes | None = None
    exported_text: str | None = None


class ExtractedContent(BaseModel):
    file_id: str
    status: ExtractionStatus
    text: str = ""
    char_count: int = 0
    extractor: str = ""
    notes: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    provenance: list[str] = Field(default_factory=list)


class DocumentProfile(BaseModel):
    """Analyzed document features used for clustering and recommendations."""

    file_id: str
    name: str
    mime_type: str
    relative_path: str
    parent_folder_id: str | None
    folder_segments: list[str] = Field(default_factory=list)
    extracted_text: str = ""
    extraction_status: ExtractionStatus = ExtractionStatus.SKIPPED
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    extraction_provenance: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    title_tokens: list[str] = Field(default_factory=list)
    semantic_text: str = ""
    operational_role: OperationalRole = OperationalRole.UNKNOWN
    temporal_tokens: list[str] = Field(default_factory=list)
    context_tokens: list[str] = Field(default_factory=list)


class SimilarityBreakdown(BaseModel):
    """Explainable similarity components for a cluster or pair."""

    semantic_score: float = Field(default=0.0, ge=0.0, le=1.0)
    lexical_score: float = Field(default=0.0, ge=0.0, le=1.0)
    context_score: float = Field(default=0.0, ge=0.0, le=1.0)
    folder_bonus: float = Field(default=0.0, ge=0.0, le=1.0)
    combined_score: float = Field(default=0.0, ge=0.0, le=1.0)


class DocumentCluster(BaseModel):
    cluster_id: str
    label: str
    member_file_ids: list[str]
    top_keywords: list[str]
    cohesion_score: float = Field(ge=0.0, le=1.0)
    rationale: str
    relationship_type: ClusterRelationship = ClusterRelationship.MIXED_SIGNALS
    operational_role: OperationalRole = OperationalRole.UNKNOWN
    similarity_breakdown: SimilarityBreakdown = Field(default_factory=SimilarityBreakdown)
    shared_signals: list[str] = Field(default_factory=list)
    distinguishing_signals: list[str] = Field(default_factory=list)


class ExistingStructureAssessment(BaseModel):
    root_folder_id: str
    coherence_score: float = Field(ge=0.0, le=1.0)
    is_well_organized: bool
    well_organized_paths: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    rationale: str


class ProposedFolder(BaseModel):
    path: str
    label: str
    cluster_id: str | None = None
    member_file_ids: list[str] = Field(default_factory=list)


class RollbackMetadata(BaseModel):
    """Snapshot fields for future rollback execution (no auto-apply in V1)."""

    snapshot_id: str = Field(default_factory=lambda: str(uuid4()))
    operation_type: str
    file_id: str
    original_path: str
    original_name: str
    proposed_path: str | None = None
    proposed_name: str | None = None
    parent_folder_id: str | None = None
    recorded_at: datetime = Field(default_factory=lambda: datetime.now())
    reversible: bool = True
    execution_deferred: bool = True


class OrganizationRecommendation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    recommendation_type: RecommendationType
    title: str
    rationale: str
    detailed_explanation: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    impacted_file_ids: list[str] = Field(default_factory=list)
    proposed_destination_path: str | None = None
    proposed_name: str | None = None
    cluster_id: str | None = None
    rollback: RollbackMetadata
    requires_approval: bool = True
    auto_apply_allowed: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class OrganizationAnalysisResult(BaseModel):
    """Full output of the organizational intelligence pipeline."""

    analysis_id: str = Field(default_factory=lambda: str(uuid4()))
    selection: FolderSelection
    preferences: AnalysisPreferences
    scanned_item_count: int
    document_count: int
    extraction_summary: dict[str, int] = Field(default_factory=dict)
    structure_assessment: ExistingStructureAssessment
    clusters: list[DocumentCluster] = Field(default_factory=list)
    proposed_folders: list[ProposedFolder] = Field(default_factory=list)
    recommendations: list[OrganizationRecommendation] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now())
