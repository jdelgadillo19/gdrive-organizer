"""Tests for persistent analysis artifacts and run comparison."""

from __future__ import annotations

import json
from pathlib import Path

from kip_core.organization.evaluation.comparison import (
    format_comparison_markdown,
)
from kip_core.organization.evaluation.metrics import build_run_metrics
from kip_core.organization.evaluation.store import (
    AnalysisArtifactStore,
    slugify_dataset_name,
)
from kip_core.organization.models import (
    AnalysisPreferences,
    FolderSelection,
)
from kip_core.organization.recommendation_engine import run_organizational_analysis

from test_organization import _messy_drive_inventory


def test_slugify_dataset_name() -> None:
    assert slugify_dataset_name("Teacher Drive Export") == "teacher-drive-export"
    assert slugify_dataset_name("messy_client_folder v2") == "messy-client-folder-v2"


def test_save_run_never_overwrites_prior_artifacts(tmp_path: Path) -> None:
    store = AnalysisArtifactStore(root=tmp_path)
    selection = FolderSelection(root_folder_id="root", root_folder_name="Root")
    items = _messy_drive_inventory()

    result1 = run_organizational_analysis(
        selection, items, AnalysisPreferences(prefer_minimal_changes=True)
    )
    paths1 = store.save_run(result1, dataset_name="invoice-archive-test")
    result2 = run_organizational_analysis(
        selection, items, AnalysisPreferences(prefer_minimal_changes=False)
    )
    paths2 = store.save_run(result2, dataset_name="invoice-archive-test")

    assert paths1.analysis_json != paths2.analysis_json
    assert Path(paths1.analysis_json).exists()
    assert Path(paths2.analysis_json).exists()

    runs = store.list_runs("invoice-archive-test")
    assert len(runs) == 2


def test_artifacts_include_metrics_and_summary(tmp_path: Path) -> None:
    store = AnalysisArtifactStore(root=tmp_path)
    selection = FolderSelection(root_folder_id="root", root_folder_name="Root")
    result = run_organizational_analysis(selection, _messy_drive_inventory())
    paths = store.save_run(result, dataset_name="messy-client-folder-v2")

    metrics = json.loads(Path(paths.metrics_json).read_text())
    assert metrics["run_id"]
    assert metrics["engine_version_hash"]
    assert metrics["extraction"]["coverage_ratio"] >= 0.0
    assert "semantic_configuration" in metrics
    assert "suppression" in metrics
    assert "false_positives" in metrics

    summary = Path(paths.summary_md).read_text()
    assert "# Libby Analysis Summary" in summary
    assert "Semantic configuration" in summary


def test_compare_two_runs(tmp_path: Path) -> None:
    store = AnalysisArtifactStore(root=tmp_path)
    selection = FolderSelection(root_folder_id="root", root_folder_name="Root")
    items = _messy_drive_inventory()

    r1 = run_organizational_analysis(
        selection, items, AnalysisPreferences(prefer_minimal_changes=True)
    )
    store.save_run(r1, dataset_name="compare-test")
    r2 = run_organizational_analysis(
        selection, items, AnalysisPreferences(prefer_minimal_changes=False)
    )
    store.save_run(r2, dataset_name="compare-test")

    report = store.compare_latest_two("compare-test")
    assert report is not None
    assert report.baseline_run_id != report.candidate_run_id
    md = format_comparison_markdown(report)
    assert "Libby Run Comparison" in md


def test_stability_metrics_on_second_run(tmp_path: Path) -> None:
    store = AnalysisArtifactStore(root=tmp_path)
    selection = FolderSelection(root_folder_id="root", root_folder_name="Root")
    items = _messy_drive_inventory()

    store.save_run(
        run_organizational_analysis(selection, items),
        dataset_name="stability-test",
    )
    paths2 = store.save_run(
        run_organizational_analysis(selection, items),
        dataset_name="stability-test",
    )
    metrics = json.loads(Path(paths2.metrics_json).read_text())
    assert metrics["stability"]["prior_run_id"] is not None
    assert metrics["stability"]["cluster_stability_score"] is not None


def test_build_run_metrics_in_memory() -> None:
    result = run_organizational_analysis(
        FolderSelection(root_folder_id="root", root_folder_name="Root"),
        _messy_drive_inventory(),
    )
    metrics = build_run_metrics(result, dataset_name="test", dataset_slug="test")
    assert metrics.recommendation_counts.total == len(result.recommendations)
    assert metrics.semantic_configuration.embedder
