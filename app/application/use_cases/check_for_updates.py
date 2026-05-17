from __future__ import annotations

import re
from typing import Any

from app.application.dto.update_info import (
    UPDATE_STATUS_AVAILABLE,
    UPDATE_STATUS_DEV_UNAVAILABLE,
    UPDATE_STATUS_ERROR,
    UPDATE_STATUS_MANUAL_ONLY,
    UPDATE_STATUS_UP_TO_DATE,
    UpdateInfoDTO,
)
from app.infrastructure.github.github_release_client import GitHubReleaseClient
from app.infrastructure.update.runtime_environment import is_packaged as runtime_is_packaged
from app.version import __version__


class CheckForUpdatesUseCase:
    def __init__(
        self,
        release_client: object | None = None,
        current_version: str = __version__,
        platform: str = "windows",
        is_packaged: bool | None = None,
    ) -> None:
        self.release_client = release_client or GitHubReleaseClient()
        self.current_version = current_version
        self.platform = platform
        self.is_packaged = runtime_is_packaged() if is_packaged is None else is_packaged

    def execute(self) -> UpdateInfoDTO:
        release_url = self._release_url()
        if not self.is_packaged:
            return UpdateInfoDTO(
                status=UPDATE_STATUS_DEV_UNAVAILABLE,
                current_version=self.current_version,
                release_url=release_url,
                platform=self.platform,
                can_auto_update=False,
                reason="Atualizacao automatica so esta disponivel em builds empacotados.",
            )

        try:
            release, manifest = self.release_client.latest_update_manifest()  # type: ignore[attr-defined]
            return self._build_update_info(release, manifest)
        except Exception as exc:  # noqa: BLE001
            return UpdateInfoDTO(
                status=UPDATE_STATUS_ERROR,
                current_version=self.current_version,
                release_url=release_url,
                platform=self.platform,
                can_auto_update=False,
                reason=str(exc),
            )

    def _build_update_info(
        self,
        release: dict[str, Any],
        manifest: dict[str, Any] | None,
    ) -> UpdateInfoDTO:
        release_url = str(
            (manifest or {}).get("release_url")
            or release.get("html_url")
            or self._release_url()
        )
        latest_version = self._latest_version(release, manifest)
        changelog = str((manifest or {}).get("notes") or release.get("body") or "")
        asset_name = str((manifest or {}).get("asset_name") or "")
        sha256 = str((manifest or {}).get("sha256") or "").strip().lower()

        if not asset_name:
            asset_name, asset_url = self._find_windows_asset(release)
        else:
            asset_url = self._find_asset_url(release, asset_name)

        if not self._is_newer(latest_version, self.current_version):
            return UpdateInfoDTO(
                status=UPDATE_STATUS_UP_TO_DATE,
                current_version=self.current_version,
                latest_version=latest_version,
                release_url=release_url,
                changelog=changelog,
                asset_name=asset_name,
                asset_url=asset_url,
                sha256=sha256,
                platform=self.platform,
                can_auto_update=False,
            )

        can_auto_update = bool(manifest and asset_name and asset_url and self._is_sha256(sha256))
        if can_auto_update:
            return UpdateInfoDTO(
                status=UPDATE_STATUS_AVAILABLE,
                current_version=self.current_version,
                latest_version=latest_version,
                release_url=release_url,
                changelog=changelog,
                asset_name=asset_name,
                asset_url=asset_url,
                sha256=sha256,
                platform=self.platform,
                can_auto_update=True,
            )

        return UpdateInfoDTO(
            status=UPDATE_STATUS_MANUAL_ONLY,
            current_version=self.current_version,
            latest_version=latest_version,
            release_url=release_url,
            changelog=changelog,
            asset_name=asset_name,
            asset_url=asset_url,
            sha256=sha256,
            platform=self.platform,
            can_auto_update=False,
            reason="Release encontrada, mas sem manifest valido com SHA-256.",
        )

    def _latest_version(self, release: dict[str, Any], manifest: dict[str, Any] | None) -> str:
        version = str((manifest or {}).get("version") or release.get("tag_name") or "").strip()
        return self._normalize_version(version)

    def _release_url(self) -> str:
        try:
            return str(self.release_client.release_url())  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            return "https://github.com/GlxV/learnkit/releases"

    def _find_asset_url(self, release: dict[str, Any], asset_name: str) -> str:
        assets = release.get("assets")
        if not isinstance(assets, list):
            return ""
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            if str(asset.get("name", "")) == asset_name:
                return str(asset.get("browser_download_url", ""))
        return ""

    def _find_windows_asset(self, release: dict[str, Any]) -> tuple[str, str]:
        assets = release.get("assets")
        if not isinstance(assets, list):
            return "", ""
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            name = str(asset.get("name", ""))
            lower = name.lower()
            if lower.endswith("-win.zip") or (lower.startswith("learnkit-") and lower.endswith(".zip")):
                return name, str(asset.get("browser_download_url", ""))
        return "", ""

    def _is_newer(self, latest: str, current: str) -> bool:
        return self._version_tuple(latest) > self._version_tuple(current)

    def _normalize_version(self, version: str) -> str:
        version = version.strip()
        if version.startswith(("v", "V")):
            version = version[1:]
        return version.split("-", 1)[0].strip()

    def _version_tuple(self, version: str) -> tuple[int, int, int]:
        normalized = self._normalize_version(version)
        parts = re.findall(r"\d+", normalized)[:3]
        while len(parts) < 3:
            parts.append("0")
        return tuple(int(part) for part in parts[:3])  # type: ignore[return-value]

    def _is_sha256(self, value: str) -> bool:
        return bool(re.fullmatch(r"[a-fA-F0-9]{64}", value))
