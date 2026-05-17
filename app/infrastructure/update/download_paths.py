from __future__ import annotations

import tempfile
from pathlib import Path


def update_cache_root() -> Path:
    return Path(tempfile.gettempdir()) / "LearnKit" / "updates"


def update_download_dir(version: str, root: Path | None = None) -> Path:
    safe_version = "".join(ch for ch in version if ch.isalnum() or ch in "._-") or "unknown"
    return (root or update_cache_root()) / safe_version
