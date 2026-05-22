"""Local filesystem scan for canonization (mirrors libby_eval conventions)."""

from __future__ import annotations

from pathlib import Path

from kip_core.organization.models import DriveMimeType, ScannedDriveItem

_MIME_BY_SUFFIX = {
    ".pdf": DriveMimeType.PDF,
    ".docx": DriveMimeType.DOCX,
    ".xlsx": DriveMimeType.XLSX,
    ".pptx": DriveMimeType.PPTX,
    ".txt": DriveMimeType.PLAIN_TEXT,
}


def resolve_corpus_root(path: Path) -> Path:
    """Accept outer extract folder or inner 'Team Development Resources' root."""
    resolved = path.resolve()
    if not resolved.is_dir():
        msg = f"Not a directory: {resolved}"
        raise FileNotFoundError(msg)
    inner = resolved / "Team Development Resources"
    if inner.is_dir():
        return inner
    return resolved


def scan_local_folder(root: Path) -> list[ScannedDriveItem]:
    items: list[ScannedDriveItem] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root))
        suffix = path.suffix.lower()
        mime = _MIME_BY_SUFFIX.get(suffix, "application/octet-stream")
        raw = path.read_bytes() if suffix in _MIME_BY_SUFFIX else None
        items.append(
            ScannedDriveItem(
                file_id=rel,
                name=path.name,
                mime_type=mime,
                relative_path=rel,
                raw_content=raw,
            )
        )
    return items
