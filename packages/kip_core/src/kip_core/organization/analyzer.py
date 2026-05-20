"""Folder scan orchestration, content extraction, and document profiling."""

from __future__ import annotations

import re
import zipfile
from collections.abc import Callable
from io import BytesIO
from xml.etree import ElementTree as ET

from kip_core.organization.models import (
    SUPPORTED_CONTENT_MIMES,
    DocumentProfile,
    DriveMimeType,
    ExtractedContent,
    ExtractionStatus,
    FolderSelection,
    ScannedDriveItem,
)
from kip_core.organization.semantic_features import enrich_profile

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "was",
        "with",
    }
)

_WORD_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def _tokenize(text: str, *, limit: int = 32) -> list[str]:
    tokens = [t.lower() for t in _WORD_RE.findall(text) if t.lower() not in _STOPWORDS]
    seen: set[str] = set()
    ordered: list[str] = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            ordered.append(token)
        if len(ordered) >= limit:
            break
    return ordered


def _ocr_pdf_pages(raw: bytes, *, max_pages: int = 3) -> tuple[str, list[str]]:
    """Optional OCR fallback when pypdf returns no text (scanned PDFs)."""
    provenance: list[str] = []
    try:
        import pytesseract  # type: ignore[import-untyped]
    except ImportError:
        return "", provenance

    try:
        from pdf2image import convert_from_bytes  # type: ignore[import-untyped]
    except ImportError:
        return "", provenance

    try:
        images = convert_from_bytes(raw, first_page=1, last_page=max_pages)
    except Exception:
        return "", provenance

    texts: list[str] = []
    for image in images:
        texts.append(pytesseract.image_to_string(image))
    provenance.append("ocr:pytesseract+pdf2image")
    return "\n".join(texts).strip(), provenance


def _extract_pdf(raw: bytes) -> ExtractedContent:
    try:
        from pypdf import PdfReader  # type: ignore[import-untyped]
    except ImportError:
        return ExtractedContent(
            file_id="",
            status=ExtractionStatus.SKIPPED,
            notes="pypdf not installed; provide exported_text or raw_content via Drive export",
            provenance=["skipped:pypdf-missing"],
        )

    reader = PdfReader(BytesIO(raw))
    pages = [page.extract_text() or "" for page in reader.pages[:50]]
    text = "\n".join(pages).strip()
    provenance = ["extract:pypdf"]
    notes = ""

    if not text:
        ocr_text, ocr_prov = _ocr_pdf_pages(raw)
        provenance.extend(ocr_prov)
        if ocr_text:
            text = ocr_text
            status = ExtractionStatus.PARTIAL
            confidence = 0.55
            notes = "Recovered text via OCR fallback for scanned PDF"
        else:
            status = ExtractionStatus.PARTIAL
            confidence = 0.15
            notes = "PDF appears scanned; install pytesseract+pdf2image for OCR fallback"
    else:
        status = ExtractionStatus.SUCCESS
        confidence = 0.85 if len(text) > 200 else 0.65

    return ExtractedContent(
        file_id="",
        status=status,
        text=text,
        char_count=len(text),
        extractor="pypdf" if "ocr" not in " ".join(provenance) else "pypdf+ocr",
        notes=notes,
        confidence=confidence,
        provenance=provenance,
    )


def _extract_docx(raw: bytes) -> ExtractedContent:
    try:
        with zipfile.ZipFile(BytesIO(raw)) as archive:
            xml_bytes = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile, OSError) as exc:
        return ExtractedContent(
            file_id="",
            status=ExtractionStatus.FAILED,
            notes=f"DOCX parse failed: {exc}",
        )

    root = ET.fromstring(xml_bytes)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for node in root.findall(".//w:t", namespace):
        if node.text:
            paragraphs.append(node.text)
    text = " ".join(paragraphs).strip()
    status = ExtractionStatus.SUCCESS if text else ExtractionStatus.PARTIAL
    return ExtractedContent(
        file_id="",
        status=status,
        text=text,
        char_count=len(text),
        extractor="stdlib-docx-xml",
        confidence=0.8 if text else 0.25,
        provenance=["extract:docx-xml"],
    )


def _extract_xlsx(raw: bytes) -> ExtractedContent:
    try:
        with zipfile.ZipFile(BytesIO(raw)) as archive:
            shared_strings_xml = archive.read("xl/sharedStrings.xml")
    except (KeyError, zipfile.BadZipFile, OSError) as exc:
        return ExtractedContent(
            file_id="",
            status=ExtractionStatus.FAILED,
            notes=f"XLSX parse failed: {exc}",
        )

    root = ET.fromstring(shared_strings_xml)
    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    cells: list[str] = []
    for node in root.findall(".//main:t", namespace):
        if node.text:
            cells.append(node.text)
    text = " ".join(cells).strip()
    status = ExtractionStatus.SUCCESS if text else ExtractionStatus.PARTIAL
    return ExtractedContent(
        file_id="",
        status=status,
        text=text,
        char_count=len(text),
        extractor="stdlib-xlsx-xml",
        confidence=0.75 if text else 0.25,
        provenance=["extract:xlsx-xml"],
    )


def _extract_pptx(raw: bytes) -> ExtractedContent:
    """Extract slide text from PPTX via Open XML."""
    texts: list[str] = []
    provenance = ["extract:pptx-xml"]
    try:
        with zipfile.ZipFile(BytesIO(raw)) as archive:
            slide_names = sorted(
                n
                for n in archive.namelist()
                if n.startswith("ppt/slides/slide") and n.endswith(".xml")
            )
            namespace = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
            for slide_name in slide_names[:40]:
                xml_bytes = archive.read(slide_name)
                root = ET.fromstring(xml_bytes)
                for node in root.findall(".//a:t", namespace):
                    if node.text:
                        texts.append(node.text)
    except (KeyError, zipfile.BadZipFile, OSError, ET.ParseError) as exc:
        return ExtractedContent(
            file_id="",
            status=ExtractionStatus.FAILED,
            notes=f"PPTX parse failed: {exc}",
            provenance=provenance,
        )

    text = " ".join(texts).strip()
    status = ExtractionStatus.SUCCESS if len(text) > 40 else ExtractionStatus.PARTIAL
    return ExtractedContent(
        file_id="",
        status=status,
        text=text,
        char_count=len(text),
        extractor="stdlib-pptx-xml",
        confidence=0.7 if len(text) > 40 else 0.35,
        provenance=provenance,
        notes="" if text else "PPTX contained little or no slide text",
    )


_EXTRACTORS: dict[str, Callable[[bytes], ExtractedContent]] = {
    DriveMimeType.PDF: _extract_pdf,
    DriveMimeType.DOCX: _extract_docx,
    DriveMimeType.XLSX: _extract_xlsx,
    DriveMimeType.PPTX: _extract_pptx,
}


def extract_content(item: ScannedDriveItem) -> ExtractedContent:
    """Extract text from supported Drive file types."""
    if item.is_folder:
        return ExtractedContent(
            file_id=item.file_id,
            status=ExtractionStatus.SKIPPED,
            notes="folders have no extractable body text",
        )

    if item.exported_text:
        text = item.exported_text.strip()
        return ExtractedContent(
            file_id=item.file_id,
            status=ExtractionStatus.SUCCESS if text else ExtractionStatus.PARTIAL,
            text=text,
            char_count=len(text),
            extractor="drive-export",
            confidence=0.9 if len(text) > 100 else 0.5,
            provenance=["extract:drive-export"],
        )

    if item.mime_type in (DriveMimeType.GOOGLE_DOC, DriveMimeType.GOOGLE_SHEET):
        return ExtractedContent(
            file_id=item.file_id,
            status=ExtractionStatus.SKIPPED,
            notes="Google native files require exported_text from Drive export API",
        )

    if item.mime_type == DriveMimeType.PLAIN_TEXT and item.raw_content:
        text = item.raw_content.decode("utf-8", errors="replace").strip()
        return ExtractedContent(
            file_id=item.file_id,
            status=ExtractionStatus.SUCCESS if text else ExtractionStatus.PARTIAL,
            text=text,
            char_count=len(text),
            extractor="plain-text",
            confidence=0.95 if text else 0.3,
            provenance=["extract:plain-text"],
        )

    if item.raw_content and item.mime_type in _EXTRACTORS:
        result = _EXTRACTORS[item.mime_type](item.raw_content)
        return result.model_copy(update={"file_id": item.file_id})

    if item.mime_type not in SUPPORTED_CONTENT_MIMES:
        return ExtractedContent(
            file_id=item.file_id,
            status=ExtractionStatus.SKIPPED,
            notes=f"unsupported mime type: {item.mime_type}",
        )

    return ExtractedContent(
        file_id=item.file_id,
        status=ExtractionStatus.SKIPPED,
        notes="no raw_content or exported_text available for extraction",
    )


def scan_items(
    items: list[ScannedDriveItem],
) -> tuple[list[ScannedDriveItem], list[ScannedDriveItem]]:
    """Partition scanned inventory into folders and analyzable documents."""
    folders = [i for i in items if i.is_folder or i.mime_type == DriveMimeType.FOLDER]
    documents = [
        i
        for i in items
        if not i.is_folder and i.mime_type != DriveMimeType.FOLDER
    ]
    return folders, documents


def build_document_profiles(
    documents: list[ScannedDriveItem],
    *,
    selection: FolderSelection,
) -> list[DocumentProfile]:
    """Run extraction and derive lightweight semantic features per document."""
    _ = selection  # reserved for scope-aware profiling extensions
    profiles: list[DocumentProfile] = []
    for item in documents:
        extracted = extract_content(item)
        combined_text = f"{item.name} {extracted.text}"
        segments = [s for s in item.relative_path.split("/") if s and s != item.name]
        keywords = _tokenize(combined_text, limit=24)
        title_tokens = _tokenize(item.name, limit=12)
        enriched = enrich_profile(item, extracted, keywords=keywords, title_tokens=title_tokens)
        profiles.append(
            DocumentProfile(
                file_id=item.file_id,
                name=item.name,
                mime_type=item.mime_type,
                relative_path=item.relative_path,
                parent_folder_id=item.parent_folder_id,
                folder_segments=segments,
                extracted_text=extracted.text,
                extraction_status=extracted.status,
                extraction_confidence=enriched["extraction_confidence"],  # type: ignore[arg-type]
                extraction_provenance=enriched["extraction_provenance"],  # type: ignore[arg-type]
                keywords=keywords,
                title_tokens=title_tokens,
                semantic_text=enriched["semantic_text"],  # type: ignore[arg-type]
                operational_role=enriched["operational_role"],  # type: ignore[arg-type]
                temporal_tokens=enriched["temporal_tokens"],  # type: ignore[arg-type]
                context_tokens=enriched["context_tokens"],  # type: ignore[arg-type]
            )
        )
    return profiles


def extraction_summary(profiles: list[DocumentProfile]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for profile in profiles:
        key = profile.extraction_status.value
        counts[key] = counts.get(key, 0) + 1
    return counts


def assess_scan_coverage(
    documents: list[ScannedDriveItem],
    profiles: list[DocumentProfile],
) -> list[str]:
    """Informational issues surfaced before recommendation generation."""
    issues: list[str] = []
    unsupported = [
        d.name
        for d in documents
        if d.mime_type not in SUPPORTED_CONTENT_MIMES
        and not d.exported_text
    ]
    if unsupported:
        issues.append(
            f"{len(unsupported)} file(s) lack supported extraction paths; "
            "recommendations will rely more on filenames and folder paths"
        )
    empty_text = [p.name for p in profiles if not p.extracted_text and not p.keywords]
    if len(empty_text) > len(profiles) * 0.5:
        issues.append(
            "most documents have little extractable text; clustering confidence may be reduced"
        )
    return issues
