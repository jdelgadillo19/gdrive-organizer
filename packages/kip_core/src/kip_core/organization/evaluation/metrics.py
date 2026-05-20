"""Build evaluation metrics and stability signals from analysis results."""

from __future__ import annotations

from datetime import UTC, datetime

from kip_core.organization.embeddings import fit_corpus_embeddings
from kip_core.organization.eval_tools import evaluate_recommendation_usefulness
from kip_core.organization.evaluation.engine_version import organization_engine_hash
from kip_core.organization.evaluation.models import (
    ExtractionStatistics,
    FalsePositiveMetrics,
    RecommendationCounts,
    RunMetrics,
    SemanticConfiguration,
    StabilityMetrics,
    SuppressionMetrics,
)
from kip_core.organization.evaluation.stability import compute_stability_vs_prior
from kip_core.organization.models import (
    DocumentProfile,
    OrganizationAnalysisResult,
    RecommendationType,
)

DEFAULT_SIMILARITY_THRESHOLD = 0.32

# Mirror clustering hybrid weights for traceability
_HYBRID_WEIGHTS = {
    "semantic": 0.52,
    "lexical": 0.23,
    "context": 0.20,
    "folder_bonus": 0.05,
}


def _extraction_ratio(result: OrganizationAnalysisResult) -> float:
    total = result.document_count or 1
    ok = result.extraction_summary.get("success", 0) + result.extraction_summary.get(
        "partial", 0
    )
    return round(ok / total, 4)


def _avg_extraction_confidence(profiles: list[DocumentProfile]) -> float:
    if not profiles:
        return 0.0
    return round(sum(p.extraction_confidence for p in profiles) / len(profiles), 4)


def _detect_embedder(profiles: list[DocumentProfile]) -> str:
    if not profiles:
        return "tfidf-local"
    model = fit_corpus_embeddings(profiles)
    return model.embedder_name


def build_semantic_configuration(
    result: OrganizationAnalysisResult,
    *,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    embedder: str | None = None,
    profiles: list[DocumentProfile] | None = None,
) -> SemanticConfiguration:
    embedder_name = embedder or (
        _detect_embedder(profiles) if profiles else "tfidf-local"
    )
    return SemanticConfiguration(
        similarity_threshold=similarity_threshold,
        hybrid_weights=dict(_HYBRID_WEIGHTS),
        embedder=embedder_name,
        preferences=result.preferences.model_dump(),
    )


def build_suppression_metrics(result: OrganizationAnalysisResult) -> SuppressionMetrics:
    proposed = len(result.proposed_folders)
    moves = sum(
        1
        for r in result.recommendations
        if r.recommendation_type == RecommendationType.FILE_MOVE
    )
    max_cap = result.preferences.max_relocation_recommendations
    estimated_suppressed = max(0, proposed - moves)
    low_conf = sum(
        1
        for r in result.recommendations
        if r.confidence_level.value == "low"
    )
    capped = max(0, moves + estimated_suppressed - max_cap) if proposed > max_cap else 0
    return SuppressionMetrics(
        proposed_folder_count=proposed,
        relocation_recommendation_count=moves,
        estimated_suppressed_relocations=estimated_suppressed,
        low_confidence_omitted_estimate=low_conf,
        capped_by_max_limits=capped,
    )


def build_false_positive_metrics(
    result: OrganizationAnalysisResult,
    *,
    profiles: list[DocumentProfile] | None = None,
) -> FalsePositiveMetrics:
    reports = evaluate_recommendation_usefulness(result, profiles=profiles)
    flagged = [r for r in reports if r.likely_false_positive]
    total = len(reports) or 1
    return FalsePositiveMetrics(
        likely_false_positive_count=len(flagged),
        false_positive_rate=round(len(flagged) / total, 4),
        flagged_titles=[r.title for r in flagged[:20]],
    )


def build_run_metrics(
    result: OrganizationAnalysisResult,
    *,
    dataset_name: str,
    dataset_slug: str,
    source_folder: str | None = None,
    profiles: list[DocumentProfile] | None = None,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    prior_metrics: RunMetrics | None = None,
    prior_clusters: list | None = None,
    prior_recommendations: list | None = None,
) -> RunMetrics:
    """Assemble full evaluation metadata for artifact persistence."""
    now = datetime.now(UTC)
    run_id = f"{now.strftime('%Y%m%dT%H%M%SZ')}-{result.analysis_id[:8]}"

    cohesion_scores = [c.cohesion_score for c in result.clusters]
    avg_cohesion = (
        round(sum(cohesion_scores) / len(cohesion_scores), 4) if cohesion_scores else 0.0
    )

    by_type: dict[str, int] = {}
    by_level: dict[str, int] = {}
    for rec in result.recommendations:
        key = rec.recommendation_type.value
        by_type[key] = by_type.get(key, 0) + 1
        lvl = rec.confidence_level.value
        by_level[lvl] = by_level.get(lvl, 0) + 1

    fp = build_false_positive_metrics(result, profiles=profiles)
    suppression = build_suppression_metrics(result)
    semantic = build_semantic_configuration(
        result,
        similarity_threshold=similarity_threshold,
        profiles=profiles,
    )

    usefulness_reports = evaluate_recommendation_usefulness(result, profiles=profiles)
    usefulness_scores = [
        r.usefulness_estimate
        for r in usefulness_reports
        if r.usefulness_estimate is not None
    ]
    avg_usefulness = (
        round(sum(usefulness_scores) / len(usefulness_scores), 4)
        if usefulness_scores
        else 0.0
    )

    stability = StabilityMetrics()
    if prior_metrics and prior_clusters is not None and prior_recommendations is not None:
        stability = compute_stability_vs_prior(
            prior_metrics=prior_metrics,
            prior_clusters=prior_clusters,
            prior_recommendations=prior_recommendations,
            candidate_clusters=result.clusters,
            candidate_recommendations=result.recommendations,
            candidate_fp_count=fp.likely_false_positive_count,
            candidate_coherence=result.structure_assessment.coherence_score,
            candidate_extraction_ratio=_extraction_ratio(result),
            candidate_avg_usefulness=avg_usefulness,
        )

    return RunMetrics(
        run_id=run_id,
        timestamp=now,
        dataset_name=dataset_name,
        dataset_slug=dataset_slug,
        source_folder=source_folder,
        engine_version_hash=organization_engine_hash(),
        analysis_id=result.analysis_id,
        document_count=result.document_count,
        scanned_item_count=result.scanned_item_count,
        cluster_count=len(result.clusters),
        average_cluster_cohesion=avg_cohesion,
        structure_coherence_score=result.structure_assessment.coherence_score,
        is_well_organized=result.structure_assessment.is_well_organized,
        extraction=ExtractionStatistics(
            summary=dict(result.extraction_summary),
            coverage_ratio=_extraction_ratio(result),
            average_extraction_confidence=_avg_extraction_confidence(profiles or []),
        ),
        recommendation_counts=RecommendationCounts(
            total=len(result.recommendations),
            by_type=by_type,
            by_confidence_level=by_level,
        ),
        suppression=suppression,
        false_positives=fp,
        semantic_configuration=semantic,
        stability=stability,
        quality_summary={
            "average_usefulness": avg_usefulness,
            "false_positive_rate": fp.false_positive_rate,
            "suppression_ratio": round(
                suppression.estimated_suppressed_relocations
                / max(1, suppression.proposed_folder_count),
                4,
            ),
        },
    )
