"""Unit tests for organizational recommendation generation."""

from kip_core.organization.analyzer import extract_content
from kip_core.organization.eval_tools import (
    debug_semantic_similarity,
    evaluate_recommendation_usefulness,
)
from kip_core.organization.models import (
    AnalysisPreferences,
    ClusterRelationship,
    ConfidenceLevel,
    DriveMimeType,
    ExtractionStatus,
    FolderSelection,
    OperationalRole,
    RecommendationType,
    ScannedDriveItem,
)
from kip_core.organization.recommendation_engine import run_organizational_analysis
from kip_core.organization.rename_rules import propose_rename
from kip_core.services.organization import OrganizationService


def _messy_drive_inventory() -> list[ScannedDriveItem]:
    return [
        ScannedDriveItem(
            file_id="file-invoice-1",
            name="invoice_2023-03-15_acme.pdf",
            mime_type=DriveMimeType.PDF,
            relative_path="invoice_2023-03-15_acme.pdf",
            exported_text="Invoice 2023 Acme Corporation payment due March",
        ),
        ScannedDriveItem(
            file_id="file-invoice-2",
            name="Invoice Acme FINAL (copy).pdf",
            mime_type=DriveMimeType.PDF,
            relative_path="Invoice Acme FINAL (copy).pdf",
            exported_text="Invoice Acme Corporation 2023 billing statement",
        ),
        ScannedDriveItem(
            file_id="file-contract",
            name="contract_v1_final_FINAL.docx",
            mime_type=DriveMimeType.DOCX,
            relative_path="misc/contract_v1_final_FINAL.docx",
            exported_text="Master services agreement contract terms and conditions",
        ),
        ScannedDriveItem(
            file_id="file-sheet",
            name="budget-2024-Q1.xlsx",
            mime_type=DriveMimeType.XLSX,
            relative_path="budget-2024-Q1.xlsx",
            exported_text="Budget forecast revenue expenses Q1 2024",
        ),
        ScannedDriveItem(
            file_id="file-notes",
            name="random notes.txt",
            mime_type=DriveMimeType.PLAIN_TEXT,
            relative_path="random notes.txt",
            exported_text="todo buy milk call dentist unrelated thoughts",
        ),
    ]


def test_pipeline_produces_clusters_and_recommendations() -> None:
    selection = FolderSelection(
        root_folder_id="folder-root",
        root_folder_name="Messy Client Folder",
    )
    result = run_organizational_analysis(
        selection,
        _messy_drive_inventory(),
        AnalysisPreferences(prefer_minimal_changes=False),
    )

    assert result.document_count == 5
    assert len(result.clusters) >= 2
    assert result.recommendations
    assert all(r.rationale for r in result.recommendations)
    assert all(r.detailed_explanation for r in result.recommendations)
    assert all(0.0 <= r.confidence_score <= 1.0 for r in result.recommendations)
    assert all(r.requires_approval for r in result.recommendations)
    assert all(not r.auto_apply_allowed for r in result.recommendations)


def test_every_recommendation_has_rollback_metadata() -> None:
    result = run_organizational_analysis(
        FolderSelection(root_folder_id="root", root_folder_name="Root"),
        _messy_drive_inventory(),
    )
    for rec in result.recommendations:
        assert rec.rollback.snapshot_id
        assert rec.rollback.reversible
        assert rec.rollback.execution_deferred
        assert rec.rollback.original_name
        assert rec.rollback.operation_type


def test_rename_recommendations_for_noisy_filenames() -> None:
    result = run_organizational_analysis(
        FolderSelection(root_folder_id="root", root_folder_name="Root"),
        _messy_drive_inventory(),
        AnalysisPreferences(enable_rename_recommendations=True),
    )
    renames = [
        r
        for r in result.recommendations
        if r.recommendation_type == RecommendationType.FILE_RENAME
    ]
    assert renames
    assert any("invoice" in r.title.lower() or "contract" in r.title.lower() for r in renames)


def test_confidence_levels_are_assigned() -> None:
    result = run_organizational_analysis(
        FolderSelection(root_folder_id="root", root_folder_name="Root"),
        _messy_drive_inventory(),
    )
    levels = {r.confidence_level for r in result.recommendations}
    assert levels.issubset({ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW})


def test_propose_rename_normalizes_noise() -> None:
    proposal = propose_rename("contract_v1_final_FINAL.docx")
    assert proposal is not None
    assert proposal.proposed_name != "contract_v1_final_FINAL.docx"
    assert "final" not in proposal.proposed_name.lower()
    assert proposal.proposed_name.endswith(".docx")


def test_organization_service_delegates_to_engine() -> None:
    service = OrganizationService()
    result = service.analyze_folder(
        FolderSelection(root_folder_id="root", root_folder_name="Root"),
        _messy_drive_inventory(),
    )
    assert result.analysis_id
    assert result.extraction_summary


def test_clusters_include_semantic_breakdown() -> None:
    result = run_organizational_analysis(
        FolderSelection(root_folder_id="root", root_folder_name="Root"),
        _messy_drive_inventory(),
    )
    assert result.clusters
    cluster = result.clusters[0]
    assert cluster.similarity_breakdown.combined_score >= 0.0
    assert cluster.relationship_type in ClusterRelationship
    assert cluster.shared_signals is not None


def test_conservative_mode_reduces_recommendation_noise() -> None:
    selection = FolderSelection(root_folder_id="root", root_folder_name="Root")
    noisy = run_organizational_analysis(
        selection,
        _messy_drive_inventory(),
        AnalysisPreferences(prefer_minimal_changes=False),
    )
    conservative = run_organizational_analysis(
        selection,
        _messy_drive_inventory(),
        AnalysisPreferences(prefer_minimal_changes=True),
    )
    assert len(conservative.recommendations) <= len(noisy.recommendations)


def test_invoice_cluster_detects_financial_role() -> None:
    result = run_organizational_analysis(
        FolderSelection(root_folder_id="root", root_folder_name="Root"),
        _messy_drive_inventory(),
        AnalysisPreferences(prefer_minimal_changes=False),
    )
    financial_clusters = [
        c for c in result.clusters if c.operational_role == OperationalRole.FINANCIAL
    ]
    assert financial_clusters


def test_eval_usefulness_reports() -> None:
    result = run_organizational_analysis(
        FolderSelection(root_folder_id="root", root_folder_name="Root"),
        _messy_drive_inventory(),
    )
    reports = evaluate_recommendation_usefulness(result)
    assert reports
    assert all(r.recommendation_id for r in reports)


def test_debug_semantic_similarity() -> None:
    from kip_core.organization.analyzer import build_document_profiles, scan_items

    items = _messy_drive_inventory()
    _folders, documents = scan_items(items)
    profiles = build_document_profiles(
        documents, selection=FolderSelection(root_folder_id="r", root_folder_name="R")
    )
    report = debug_semantic_similarity(
        profiles, "file-invoice-1", "file-invoice-2"
    )
    assert report["combined_score"] >= 0.0
    assert "embedder" in report


def test_pptx_extraction_from_minimal_archive() -> None:
    import zipfile
    from io import BytesIO

    buffer = BytesIO()
    slide_xml = (
        '<?xml version="1.0"?>'
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        "<p:cSld><p:spTree><a:sp><a:txBody><a:p><a:r><a:t>Quarterly Review</a:t>"
        "</a:r></a:p></a:txBody></a:sp></p:spTree></p:cSld></p:sld>"
    )
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("ppt/slides/slide1.xml", slide_xml)
    item = ScannedDriveItem(
        file_id="deck-1",
        name="review.pptx",
        mime_type=DriveMimeType.PPTX,
        relative_path="review.pptx",
        raw_content=buffer.getvalue(),
    )
    extracted = extract_content(item)
    assert extracted.status in {ExtractionStatus.SUCCESS, ExtractionStatus.PARTIAL}
    assert "Quarterly" in extracted.text
    assert extracted.confidence > 0.0
    assert extracted.provenance
