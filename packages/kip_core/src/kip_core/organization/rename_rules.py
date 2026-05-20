"""Conservative filename normalization recommendations."""

from __future__ import annotations

import re
from dataclasses import dataclass

_DATE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(\d{4})[-_](\d{1,2})[-_](\d{1,2})\b"), "ymd"),
    (re.compile(r"\b(\d{1,2})[-_/](\d{1,2})[-_/](\d{4})\b"), "mdy"),
]

_NOISE_RE = re.compile(r"\s+")
_SEGMENT_SPLIT_RE = re.compile(r"[_\s.-]+")
_NOISE_SEGMENTS = frozenset({"v1", "v2", "v3", "final", "copy", "draft", "temp"})
_EXTENSION_RE = re.compile(r"(\.[^.]+)$")


@dataclass(frozen=True)
class RenameProposal:
    file_id: str
    original_name: str
    proposed_name: str
    rationale: str
    signals: list[str]


def _normalize_date(name: str) -> tuple[str, list[str]]:
    signals: list[str] = []
    updated = name
    for pattern, fmt in _DATE_PATTERNS:
        match = pattern.search(updated)
        if not match:
            continue
        if fmt == "ymd":
            year, month, day = match.groups()
        else:
            month, day, year = match.groups()
        normalized = f"{year}-{int(month):02d}-{int(day):02d}"
        updated = updated[: match.start()] + normalized + updated[match.end() :]
        signals.append(f"normalized date to {normalized}")
        break
    return updated, signals


def _normalize_tokens(stem: str) -> tuple[str, list[str]]:
    signals: list[str] = []
    cleaned = _NOISE_RE.sub(" ", stem.replace("_", " ").replace("-", " ")).strip()
    if cleaned != stem:
        signals.append("replaced separators with spaces")
    title = " ".join(word.capitalize() if word.islower() else word for word in cleaned.split())
    if title != cleaned:
        signals.append("applied consistent title casing")
    return title, signals


def propose_rename(profile_name: str, *, cluster_label: str | None = None) -> RenameProposal | None:
    """Return a rename proposal when normalization improves clarity without collisions."""
    extension_match = _EXTENSION_RE.search(profile_name)
    extension = extension_match.group(1) if extension_match else ""
    stem = profile_name[: -len(extension)] if extension else profile_name

    segments = [s for s in _SEGMENT_SPLIT_RE.split(stem) if s]
    has_noise = any(s.lower() in _NOISE_SEGMENTS for s in segments) or "  " in stem or "_" in stem
    if not has_noise:
        return None

    working = stem
    all_signals: list[str] = []

    dated, date_signals = _normalize_date(working)
    working = dated
    all_signals.extend(date_signals)

    filtered_segments = [
        s for s in _SEGMENT_SPLIT_RE.split(working) if s and s.lower() not in _NOISE_SEGMENTS
    ]
    if filtered_segments:
        deduped = " ".join(filtered_segments)
        if deduped != working:
            all_signals.append("removed noisy version or copy markers")
        working = deduped

    titled, token_signals = _normalize_tokens(working)
    working = titled
    all_signals.extend(token_signals)

    working = _NOISE_RE.sub(" ", working).strip()
    proposed_stem = working or stem
    proposed_name = f"{proposed_stem}{extension}"

    if proposed_name == profile_name:
        return None

    rationale_parts = [
        "Filename normalization improves scanability and consistency.",
        *all_signals,
    ]
    if cluster_label:
        rationale_parts.append(f"aligns with cluster theme: {cluster_label}")

    return RenameProposal(
        file_id="",
        original_name=profile_name,
        proposed_name=proposed_name,
        rationale=" ".join(rationale_parts),
        signals=all_signals,
    )


def propose_renames_for_profiles(
    profiles: list,
    cluster_by_file: dict[str, str],
) -> list[RenameProposal]:
    proposals: list[RenameProposal] = []
    seen_names: set[str] = set()

    for profile in profiles:
        label = cluster_by_file.get(profile.file_id)
        proposal = propose_rename(profile.name, cluster_label=label)
        if proposal is None:
            seen_names.add(profile.name.lower())
            continue
        if proposal.proposed_name.lower() in seen_names:
            continue
        seen_names.add(proposal.proposed_name.lower())
        proposals.append(
            RenameProposal(
                file_id=profile.file_id,
                original_name=proposal.original_name,
                proposed_name=proposal.proposed_name,
                rationale=proposal.rationale,
                signals=proposal.signals,
            )
        )
    return proposals
