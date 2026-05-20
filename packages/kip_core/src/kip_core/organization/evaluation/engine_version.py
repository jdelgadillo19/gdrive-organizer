"""Organization engine version fingerprint for reproducibility."""

from __future__ import annotations

import hashlib
from pathlib import Path


def organization_engine_hash() -> str:
    """Short hash of organization engine source files."""
    org_dir = Path(__file__).resolve().parent.parent
    digest = hashlib.sha256()
    for path in sorted(org_dir.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    eval_dir = org_dir / "evaluation"
    if eval_dir.is_dir():
        for path in sorted(eval_dir.glob("*.py")):
            digest.update(path.name.encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()[:12]
