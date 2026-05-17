from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.version import GITHUB_RELEASES_URL, GITHUB_REPO


class GitHubReleaseError(RuntimeError):
    pass


class GitHubReleaseClient:
    def __init__(self, repo: str = GITHUB_REPO, timeout: int = 10) -> None:
        self.repo = repo
        self.timeout = timeout
        self.api_url = f"https://api.github.com/repos/{repo}/releases/latest"

    def release_url(self) -> str:
        return f"https://github.com/{self.repo}/releases" if self.repo else GITHUB_RELEASES_URL

    def latest_release(self) -> dict[str, Any]:
        return self._read_json(self.api_url)

    def latest_update_manifest(self) -> tuple[dict[str, Any], dict[str, Any] | None]:
        release = self.latest_release()
        manifest_asset = self._find_manifest_asset(release)
        if manifest_asset is None:
            return release, None

        url = str(manifest_asset.get("browser_download_url", ""))
        if not url:
            raise GitHubReleaseError("Manifest asset does not include a download URL.")
        manifest = self._read_json(url)
        self._validate_manifest(manifest)
        return release, manifest

    def _read_json(self, url: str) -> dict[str, Any]:
        request = Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "LearnKit-Updater",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                payload = response.read()
        except (HTTPError, URLError, OSError) as exc:
            raise GitHubReleaseError(f"Could not read GitHub release data: {exc}") from exc

        try:
            data = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GitHubReleaseError(f"Invalid GitHub JSON response: {exc}") from exc
        if not isinstance(data, dict):
            raise GitHubReleaseError("GitHub JSON response must be an object.")
        return data

    def _find_manifest_asset(self, release: dict[str, Any]) -> dict[str, Any] | None:
        assets = release.get("assets")
        if not isinstance(assets, list):
            return None
        for preferred in ("latest.json", "manifest.json"):
            for asset in assets:
                if not isinstance(asset, dict):
                    continue
                if str(asset.get("name", "")).lower() == preferred:
                    return asset
        return None

    def _validate_manifest(self, manifest: dict[str, Any]) -> None:
        required = ["version", "platform", "asset_name", "sha256", "release_url"]
        missing = [field for field in required if not str(manifest.get(field, "")).strip()]
        if missing:
            raise GitHubReleaseError(f"Manifest is missing fields: {', '.join(missing)}")
