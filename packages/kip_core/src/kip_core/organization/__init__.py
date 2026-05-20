"""Organizational intelligence engine — recommendation-first, human-approved."""

from kip_core.organization.eval_tools import (
    debug_semantic_similarity,
    evaluate_recommendation_usefulness,
    format_cluster_report,
    inspect_clusters,
    recluster_for_debug,
)
from kip_core.organization.models import (
    AnalysisPreferences,
    FolderSelection,
    OrganizationAnalysisResult,
    OrganizationRecommendation,
    ScannedDriveItem,
)
from kip_core.organization.evaluation import (
    AnalysisArtifactStore,
    compare_analysis_runs,
    default_analysis_root,
    render_summary_markdown,
    slugify_dataset_name,
)
from kip_core.organization.recommendation_engine import run_organizational_analysis

__all__ = [
    "AnalysisArtifactStore",
    "AnalysisPreferences",
    "FolderSelection",
    "OrganizationAnalysisResult",
    "OrganizationRecommendation",
    "ScannedDriveItem",
    "compare_analysis_runs",
    "debug_semantic_similarity",
    "default_analysis_root",
    "evaluate_recommendation_usefulness",
    "format_cluster_report",
    "inspect_clusters",
    "recluster_for_debug",
    "render_summary_markdown",
    "run_organizational_analysis",
    "slugify_dataset_name",
]
