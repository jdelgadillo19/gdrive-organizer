"""Canonization workflow models for LaunchBuild1."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field

from kip_core.domain.governance import AuthorityLevel


class CanonTopicId(StrEnum):
    ROLE_DESCRIPTIONS = "role_descriptions"
    MASTER_SUNDAY_SERVICE_PLAN = "master_sunday_service_plan"
    WEEKLY_PREP_PLAN = "weekly_prep_plan"
    NEW_VOLUNTEER_ONBOARDING = "new_volunteer_onboarding"
    UNASSIGNED = "unassigned"


class CrossReferenceKind(StrEnum):
    SAME_TOPIC_RECONCILE = "same_topic_reconcile"
    NEAR_DUPLICATE = "near_duplicate"
    PURPOSE_COLLISION = "purpose_collision"


class ConflictSeverity(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CanonDocumentCandidate(BaseModel):
    file_id: str
    name: str
    relative_path: str
    topic_id: CanonTopicId
    match_score: float
    match_reasons: list[str] = Field(default_factory=list)
    recommended_canon: bool = False
    authority_level: AuthorityLevel = AuthorityLevel.DRAFT


class CrossReferenceIssue(BaseModel):
    kind: CrossReferenceKind
    file_a: str
    file_b: str
    title_a: str
    title_b: str
    similarity: float
    severity: ConflictSeverity
    summary: str
    contradiction_signals: list[str] = Field(default_factory=list)


class CanonTopicResult(BaseModel):
    topic_id: CanonTopicId
    title: str
    description: str
    candidates: list[CanonDocumentCandidate]
    recommended_file_id: str | None = None
    gap: bool = False
    gap_message: str | None = None


class CanonizationResult(BaseModel):
    corpus_root: str
    canon_folder_relative: str = "Canon"
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    topics: list[CanonTopicResult]
    cross_reference_issues: list[CrossReferenceIssue] = Field(default_factory=list)
    near_duplicate_groups: list[list[str]] = Field(default_factory=list)
    unassigned_documents: list[str] = Field(default_factory=list)
    extraction_coverage_ratio: float = 0.0
