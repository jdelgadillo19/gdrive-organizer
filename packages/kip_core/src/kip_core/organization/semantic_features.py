"""Contextual semantic feature extraction for organizational clustering."""

from __future__ import annotations

import re
from datetime import datetime

from kip_core.organization.models import (
    DocumentProfile,
    ExtractedContent,
    OperationalRole,
    ScannedDriveItem,
)

_ROLE_KEYWORDS: dict[OperationalRole, frozenset[str]] = {
    OperationalRole.FINANCIAL: frozenset(
        {"invoice", "billing", "payment", "receipt", "budget", "expense", "payroll", "tax"}
    ),
    OperationalRole.LEGAL: frozenset(
        {"contract", "agreement", "terms", "nda", "compliance", "policy", "license", "waiver"}
    ),
    OperationalRole.OPERATIONS: frozenset(
        {"process", "workflow", "runbook", "procedure", "operations", "onboarding", "checklist"}
    ),
    OperationalRole.PLANNING: frozenset(
        {"roadmap", "strategy", "plan", "forecast", "initiative", "okr", "milestone"}
    ),
    OperationalRole.REPORTING: frozenset(
        {"report", "summary", "dashboard", "metrics", "analysis", "quarterly", "annual"}
    ),
}

_MIME_ROLE_HINTS: dict[str, OperationalRole] = {
    "spreadsheet": OperationalRole.FINANCIAL,
    "presentation": OperationalRole.REPORTING,
}

_DATE_IN_NAME_RE = re.compile(
    r"\b(\d{4})[-_](\d{1,2})[-_](\d{1,2})\b|\b(\d{1,2})[-_/](\d{1,2})[-_/](\d{4})\b"
)
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_QUARTER_RE = re.compile(r"\bQ[1-4]\b", re.IGNORECASE)


def _infer_operational_role(
    *,
    keywords: list[str],
    title_tokens: list[str],
    folder_segments: list[str],
    mime_type: str,
) -> OperationalRole:
    """Distinguish operational role from shared vocabulary alone."""
    token_set = set(keywords) | set(title_tokens) | {s.lower() for s in folder_segments}
    scores: dict[OperationalRole, int] = {}
    for role, role_words in _ROLE_KEYWORDS.items():
        overlap = len(token_set & role_words)
        if overlap:
            scores[role] = overlap

    for hint_key, role in _MIME_ROLE_HINTS.items():
        if hint_key in mime_type.lower():
            scores[role] = scores.get(role, 0) + 1

    if not scores:
        return OperationalRole.GENERAL if token_set else OperationalRole.UNKNOWN
    return max(scores, key=scores.get)


def _extract_temporal_tokens(name: str, text: str) -> list[str]:
    combined = f"{name} {text}"
    tokens: list[str] = []
    for match in _DATE_IN_NAME_RE.finditer(combined):
        tokens.append(match.group(0).replace("_", "-"))
    for match in _YEAR_RE.finditer(combined):
        tokens.append(match.group(0))
    for match in _QUARTER_RE.finditer(combined):
        tokens.append(match.group(0).upper())
    if not tokens and "modified" not in combined.lower():
        return tokens
    return list(dict.fromkeys(tokens))[:6]


def _context_tokens_from_path(folder_segments: list[str], mime_type: str) -> list[str]:
    tokens: list[str] = []
    for segment in folder_segments:
        cleaned = re.sub(r"[^a-z0-9]+", " ", segment.lower()).strip()
        tokens.extend(cleaned.split())
    mime_tail = mime_type.rsplit(".", maxsplit=1)[-1].replace("+", " ")
    if mime_tail:
        tokens.append(mime_tail.lower())
    return list(dict.fromkeys(tokens))[:12]


def build_semantic_text(
    *,
    name: str,
    extracted_text: str,
    folder_segments: list[str],
    operational_role: OperationalRole,
    temporal_tokens: list[str],
) -> str:
    """Single embedding input combining content, path, and inferred role."""
    path_text = " / ".join(folder_segments)
    temporal_text = " ".join(temporal_tokens)
    return (
        f"role:{operational_role.value} path:{path_text} time:{temporal_text} "
        f"title:{name} content:{extracted_text}"
    ).strip()


def enrich_profile(
    item: ScannedDriveItem,
    extracted: ExtractedContent,
    *,
    keywords: list[str],
    title_tokens: list[str],
) -> dict[str, object]:
    """Derive contextual features beyond raw lexical tokens."""
    segments = [s for s in item.relative_path.split("/") if s and s != item.name]
    operational_role = _infer_operational_role(
        keywords=keywords,
        title_tokens=title_tokens,
        folder_segments=segments,
        mime_type=item.mime_type,
    )
    temporal_tokens = _extract_temporal_tokens(item.name, extracted.text)
    context_tokens = _context_tokens_from_path(segments, item.mime_type)
    semantic_text = build_semantic_text(
        name=item.name,
        extracted_text=extracted.text,
        folder_segments=segments,
        operational_role=operational_role,
        temporal_tokens=temporal_tokens,
    )
    return {
        "operational_role": operational_role,
        "temporal_tokens": temporal_tokens,
        "context_tokens": context_tokens,
        "semantic_text": semantic_text,
        "extraction_confidence": extracted.confidence,
        "extraction_provenance": extracted.provenance,
    }


def profiles_share_operational_role(a: DocumentProfile, b: DocumentProfile) -> bool:
    return (
        a.operational_role == b.operational_role
        and a.operational_role not in {OperationalRole.UNKNOWN, OperationalRole.GENERAL}
    )


def average_extraction_confidence(profiles: list[DocumentProfile]) -> float:
    if not profiles:
        return 0.0
    return round(sum(p.extraction_confidence for p in profiles) / len(profiles), 4)


def modified_year(item: ScannedDriveItem) -> int | None:
    if item.modified_at is None:
        return None
    return item.modified_at.year if isinstance(item.modified_at, datetime) else None
