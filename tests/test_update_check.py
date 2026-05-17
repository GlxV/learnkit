from __future__ import annotations

from app.application.dto.update_info import (
    UPDATE_STATUS_AVAILABLE,
    UPDATE_STATUS_DEV_UNAVAILABLE,
    UPDATE_STATUS_ERROR,
    UPDATE_STATUS_MANUAL_ONLY,
    UPDATE_STATUS_UP_TO_DATE,
)
from app.application.use_cases.check_for_updates import CheckForUpdatesUseCase


class FakeReleaseClient:
    def __init__(self, release: dict[str, object], manifest: dict[str, object] | None) -> None:
        self.release = release
        self.manifest = manifest
        self.called = False

    def latest_update_manifest(self) -> tuple[dict[str, object], dict[str, object] | None]:
        self.called = True
        return self.release, self.manifest

    def release_url(self) -> str:
        return "https://github.com/GlxV/learnkit/releases"


class FailingReleaseClient:
    def latest_update_manifest(self) -> tuple[dict[str, object], dict[str, object] | None]:
        raise OSError("offline")

    def release_url(self) -> str:
        return "https://github.com/GlxV/learnkit/releases"


def _release(version: str = "v0.2.0") -> dict[str, object]:
    return {
        "tag_name": version,
        "html_url": f"https://github.com/GlxV/learnkit/releases/tag/{version}",
        "body": "Release notes",
        "assets": [
            {
                "name": "LearnKit-0.2.0-win.zip",
                "browser_download_url": "https://example.test/LearnKit-0.2.0-win.zip",
            }
        ],
    }


def _manifest(version: str = "0.2.0") -> dict[str, object]:
    return {
        "version": version,
        "platform": "windows",
        "asset_name": "LearnKit-0.2.0-win.zip",
        "sha256": "a" * 64,
        "release_url": "https://github.com/GlxV/learnkit/releases/tag/v0.2.0",
        "notes": "Manifest notes",
    }


def test_update_check_reports_dev_mode_without_calling_github() -> None:
    client = FakeReleaseClient(_release(), _manifest())
    use_case = CheckForUpdatesUseCase(
        release_client=client,
        current_version="0.1.0",
        is_packaged=False,
    )

    info = use_case.execute()

    assert info.status == UPDATE_STATUS_DEV_UNAVAILABLE
    assert info.can_auto_update is False
    assert client.called is False


def test_update_check_reports_up_to_date_when_versions_match() -> None:
    client = FakeReleaseClient(_release("v0.2.0"), _manifest("0.2.0"))
    use_case = CheckForUpdatesUseCase(
        release_client=client,
        current_version="0.2.0",
        is_packaged=True,
    )

    info = use_case.execute()

    assert info.status == UPDATE_STATUS_UP_TO_DATE
    assert info.can_auto_update is False
    assert info.current_version == "0.2.0"
    assert info.latest_version == "0.2.0"


def test_update_check_reports_installable_update_when_manifest_has_hash() -> None:
    client = FakeReleaseClient(_release(), _manifest())
    use_case = CheckForUpdatesUseCase(
        release_client=client,
        current_version="0.1.0",
        is_packaged=True,
    )

    info = use_case.execute()

    assert info.status == UPDATE_STATUS_AVAILABLE
    assert info.can_auto_update is True
    assert info.latest_version == "0.2.0"
    assert info.asset_name == "LearnKit-0.2.0-win.zip"
    assert info.asset_url == "https://example.test/LearnKit-0.2.0-win.zip"
    assert info.sha256 == "a" * 64
    assert info.changelog == "Manifest notes"


def test_update_check_reports_manual_only_when_release_has_no_manifest() -> None:
    client = FakeReleaseClient(_release(), None)
    use_case = CheckForUpdatesUseCase(
        release_client=client,
        current_version="0.1.0",
        is_packaged=True,
    )

    info = use_case.execute()

    assert info.status == UPDATE_STATUS_MANUAL_ONLY
    assert info.can_auto_update is False
    assert info.asset_name == "LearnKit-0.2.0-win.zip"
    assert info.asset_url == "https://example.test/LearnKit-0.2.0-win.zip"
    assert info.sha256 == ""


def test_update_check_turns_client_errors_into_controlled_status() -> None:
    use_case = CheckForUpdatesUseCase(
        release_client=FailingReleaseClient(),
        current_version="0.1.0",
        is_packaged=True,
    )

    info = use_case.execute()

    assert info.status == UPDATE_STATUS_ERROR
    assert info.can_auto_update is False
    assert "offline" in info.reason
