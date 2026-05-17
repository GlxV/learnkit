from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


UPDATE_STATUS_UP_TO_DATE = "up_to_date"
UPDATE_STATUS_AVAILABLE = "update_available"
UPDATE_STATUS_DEV_UNAVAILABLE = "dev_mode_unavailable"
UPDATE_STATUS_MANUAL_ONLY = "manual_only"
UPDATE_STATUS_ERROR = "error"


@dataclass(frozen=True)
class UpdateInfoDTO:
    status: str
    current_version: str
    latest_version: str = ""
    release_url: str = ""
    changelog: str = ""
    asset_name: str = ""
    asset_url: str = ""
    sha256: str = ""
    platform: str = "windows"
    can_auto_update: bool = False
    reason: str = ""


@dataclass(frozen=True)
class DownloadedUpdateDTO:
    version: str
    package_path: Path
    asset_name: str
    sha256: str
    size_bytes: int
