"""Persistent analysis artifacts, run comparison, and evaluation traceability."""

from kip_core.organization.evaluation.comparison import compare_analysis_runs
from kip_core.organization.evaluation.models import (
    AnalysisRunArtifactPaths,
    RunComparisonReport,
    RunMetrics,
    RunRecord,
    SemanticConfiguration,
    StabilityMetrics,
)
from kip_core.organization.evaluation.store import (
    AnalysisArtifactStore,
    default_analysis_root,
    slugify_dataset_name,
)
from kip_core.organization.evaluation.summary import render_summary_markdown

__all__ = [
    "AnalysisArtifactStore",
    "AnalysisRunArtifactPaths",
    "RunComparisonReport",
    "RunMetrics",
    "RunRecord",
    "SemanticConfiguration",
    "StabilityMetrics",
    "compare_analysis_runs",
    "default_analysis_root",
    "render_summary_markdown",
    "slugify_dataset_name",
]
