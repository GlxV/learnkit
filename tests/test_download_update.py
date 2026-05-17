from __future__ import annotations

import hashlib
import io

import pytest

from app.application.dto.update_info import UpdateInfoDTO
from app.application.use_cases.download_update import DownloadUpdateError, DownloadUpdateUseCase


class FakeResponse(io.BytesIO):
    def __init__(self, payload: bytes) -> None:
        super().__init__(payload)
        self.headers = {"Content-Length": str(len(payload))}

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.close()


def _update_info(payload: bytes, sha256: str | None = None) -> UpdateInfoDTO:
    return UpdateInfoDTO(
        status="update_available",
        current_version="0.1.0",
        latest_version="0.2.0",
        release_url="https://github.com/GlxV/learnkit/releases/tag/v0.2.0",
        changelog="notes",
        asset_name="LearnKit-0.2.0-win.zip",
        asset_url="https://example.test/LearnKit-0.2.0-win.zip",
        sha256=sha256 or hashlib.sha256(payload).hexdigest(),
        platform="windows",
        can_auto_update=True,
    )


def test_download_update_writes_zip_after_sha256_validation(tmp_path) -> None:
    payload = b"learnkit release zip"
    calls: list[tuple[int, int | None, int | None]] = []
    use_case = DownloadUpdateUseCase(
        download_root=tmp_path,
        opener=lambda url, timeout=30: FakeResponse(payload),
    )

    downloaded = use_case.execute(
        _update_info(payload),
        progress_callback=lambda done, total, percent: calls.append((done, total, percent)),
    )

    assert downloaded.version == "0.2.0"
    assert downloaded.package_path.exists()
    assert downloaded.package_path.suffix == ".zip"
    assert downloaded.package_path.read_bytes() == payload
    assert downloaded.sha256 == hashlib.sha256(payload).hexdigest()
    assert calls[0] == (0, len(payload), 0)
    assert calls[-1] == (len(payload), len(payload), 100)
    assert not downloaded.package_path.with_suffix(".zip.download").exists()


def test_download_update_rejects_hash_mismatch(tmp_path) -> None:
    payload = b"learnkit release zip"
    use_case = DownloadUpdateUseCase(
        download_root=tmp_path,
        opener=lambda url, timeout=30: FakeResponse(payload),
    )

    with pytest.raises(DownloadUpdateError, match="SHA-256"):
        use_case.execute(_update_info(payload, sha256="b" * 64))

    assert not list(tmp_path.rglob("*.zip"))
    assert not list(tmp_path.rglob("*.download"))


def test_download_update_rejects_non_installable_update(tmp_path) -> None:
    payload = b"learnkit release zip"
    info = _update_info(payload)
    info = UpdateInfoDTO(**{**info.__dict__, "can_auto_update": False})
    use_case = DownloadUpdateUseCase(
        download_root=tmp_path,
        opener=lambda url, timeout=30: FakeResponse(payload),
    )

    with pytest.raises(DownloadUpdateError, match="not installable"):
        use_case.execute(info)
