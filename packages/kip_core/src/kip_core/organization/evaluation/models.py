"""Pydantic schemas for analysis artifacts and run comparison."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SemanticConfiguration(BaseModel):
    """Thresholds and weights used for a single analysis run."""

    similarity_threshold: float
    hybrid_weights: dict[str, float] = Field(default_factory=dict)
    embedder: str = "tfidf-local"
    preferences: dict[str, Any] = Field(default_factory=dict)


class SuppressionMetrics(BaseModel):
    """Estimates of recommendations filtered by conservative heuristics."""

    proposed_folder_count: int = 0
    relocation_recommendation_count: int = 0
    estimated_suppressed_relocations: int = 0
    low_confidence_omitted_estimate: int = 0
    capped_by_max_limits: int = 0


class FalsePositiveMetrics(BaseModel):
    likely_false_positive_count: int = 0
    false_positive_rate: float = Field(ge=0.0, le=1.0)
    flagged_titles: list[str] = Field(default_factory=list)


class RecommendationCounts(BaseModel):
    total: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)
    by_confidence_level: dict[str, int] = Field(default_factory=dict)


class ExtractionStatistics(BaseModel):
    summary: dict[str, int] = Field(default_factory=dict)
    coverage_ratio: float = Field(ge=0.0, le=1.0)
    average_extraction_confidence: float = Field(ge=0.0, le=1.0)


class StabilityMetrics(BaseModel):
    """Comparison to the immediately prior run on the same dataset, when available."""

    prior_run_id: str | None = None
    prior_run_timestamp: datetime | None = None
    cluster_stability_score: float | None = Field(
        default=None,
        description="Jaccard overlap of cluster member sets (0-1)",
    )
    recommendation_churn_rate: float | None = Field(
        default=None,
        description="Share of recommendation fingerprints that changed",
    )
    repeat_recommendation_rate: float | None = Field(
        default=None,
        description="Share of prior recommendations still present",
    )
    usefulness_trend_delta: float | None = None
    false_positive_delta: int | None = None
    coherence_delta: float | None = None
    extraction_coverage_delta: float | None = None


class RunMetrics(BaseModel):
    """Evaluation metadata persisted alongside each analysis run."""

    run_id: str
    timestamp: datetime
    dataset_name: str
    dataset_slug: str
    source_folder: str | None = None
    engine_version_hash: str
    analysis_id: str
    document_count: int
    scanned_item_count: int
    cluster_count: int
    average_cluster_cohesion: float = Field(ge=0.0, le=1.0)
    structure_coherence_score: float = Field(ge=0.0, le=1.0)
    is_well_organized: bool
    extraction: ExtractionStatistics
    recommendation_counts: RecommendationCounts
    suppression: SuppressionMetrics
    false_positives: FalsePositiveMetrics
    semantic_configuration: SemanticConfiguration
    stability: StabilityMetrics = Field(default_factory=StabilityMetrics)
    quality_summary: dict[str, float] = Field(default_factory=dict)


class RunRecord(BaseModel):
    """Index entry for a persisted run (stored in runs-index.json)."""

    run_id: str
    timestamp: datetime
    date_partition: str
    artifact_stem: str
    paths: dict[str, str]
    metrics_snapshot: dict[str, int | float | str | bool] = Field(default_factory=dict)


class AnalysisRunArtifactPaths(BaseModel):
    """Filesystem paths for a single immutable analysis run."""

    run_id: str
    timestamp: datetime
    dataset_slug: str
    date_partition: str
    artifact_stem: str
    run_directory: str
    analysis_json: str
    clusters_json: str
    metrics_json: str
    summary_md: str


class RunComparisonReport(BaseModel):
    """Delta report between two analysis runs on the same or different datasets."""

    baseline_run_id: str
    candidate_run_id: str
    baseline_timestamp: datetime
    candidate_timestamp: datetime
    dataset_baseline: str
    dataset_candidate: str
    recommendation_count_delta: int
    recommendation_count_delta_by_type: dict[str, int] = Field(default_factory=dict)
    cluster_count_delta: int
    coherence_delta: float
    extraction_coverage_delta: float
    false_positive_delta: int
    cluster_stability_score: float
    recommendation_churn_rate: float
    repeat_recommendation_rate: float
    semantic_drift: dict[str, Any] = Field(default_factory=dict)
    new_recommendations: list[str] = Field(default_factory=list)
    removed_recommendations: list[str] = Field(default_factory=list)
    notable_changes: list[str] = Field(default_factory=list)
