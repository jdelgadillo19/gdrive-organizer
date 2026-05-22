"""Tests for LaunchBuild1 canonization."""

from __future__ import annotations

from pathlib import Path

import pytest

from kip_core.canon.engine import run_canonization
from kip_core.canon.models import CanonTopicId
from kip_core.canon.matcher import assign_topic
from kip_core.canon.scan import scan_local_folder
from kip_core.organization.analyzer import build_document_profiles, scan_items
from kip_core.organization.models import (
    DriveMimeType,
    ExtractionStatus,
    FolderSelection,
    ScannedDriveItem,
)


def _item(rel: str, name: str) -> ScannedDriveItem:
    return ScannedDriveItem(
        file_id=rel,
        name=name,
        mime_type=DriveMimeType.DOCX,
        relative_path=rel,
        raw_content=None,
    )


def test_assign_topic_onboarding_path() -> None:
    items = [
        _item(
            "New Volunteer Onboarding/Music Team/Audition Process.docx",
            "Audition Process.docx",
        )
    ]
    _folders, documents = scan_items(items)
    profiles = build_document_profiles(
        documents,
        selection=FolderSelection(root_folder_id="r", root_folder_name="r"),
    )
    profiles[0].extracted_text = "new volunteer onboarding audition process training"
    profiles[0].extraction_status = ExtractionStatus.SUCCESS
    cand = assign_topic(profiles[0])
    assert cand.topic_id == CanonTopicId.NEW_VOLUNTEER_ONBOARDING


def test_run_canonization_on_team_development_corpus() -> None:
    desktop = Path("/Users/jessedelgadillo/Desktop")
    roots = list(desktop.glob("Team Development Resources-20260522T142219Z-3-001"))
    if not roots:
        pytest.skip("Team Development corpus not present on Desktop")

    extract_root = roots[0]
    inner = extract_root / "Team Development Resources"
    corpus = inner if inner.is_dir() else extract_root

    result = run_canonization(corpus)
    assert result.extraction_coverage_ratio > 0.1
    assert len(result.topics) == 4

    topic_ids = {t.topic_id for t in result.topics}
    assert CanonTopicId.ROLE_DESCRIPTIONS in topic_ids
    assert CanonTopicId.NEW_VOLUNTEER_ONBOARDING in topic_ids

    gaps = [t for t in result.topics if t.gap]
    assert len(gaps) <= 2, f"Too many gaps: {[g.title for g in gaps]}"

    onboarding = next(t for t in result.topics if t.topic_id == CanonTopicId.NEW_VOLUNTEER_ONBOARDING)
    assert onboarding.recommended_file_id is not None


def test_scan_local_folder_finds_docx(tmp_path: Path) -> None:
    doc = tmp_path / "Leadership Roles.docx"
    doc.write_bytes(b"")
    items = scan_local_folder(tmp_path)
    assert len(items) == 1
    assert items[0].name == "Leadership Roles.docx"
