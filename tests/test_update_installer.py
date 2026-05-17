from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pytest

from app.infrastructure.update.update_installer import (
    UpdateInstallError,
    install_update,
    safe_extract_zip,
)


def _make_zip(path: Path, files: dict[str, bytes]) -> str:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in files.items():
            archive.writestr(name, payload)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_safe_extract_zip_blocks_zip_slip(tmp_path) -> None:
    package = tmp_path / "bad.zip"
    _make_zip(package, {"../evil.txt": b"nope"})

    with pytest.raises(UpdateInstallError, match="unsafe"):
        safe_extract_zip(package, tmp_path / "staging")


def test_install_update_replaces_app_files_and_preserves_user_data(tmp_path) -> None:
    install_dir = tmp_path / "install"
    install_dir.mkdir()
    (install_dir / "LearnKit.exe").write_bytes(b"old exe")
    (install_dir / "_internal").mkdir()
    (install_dir / "_internal" / "old.txt").write_text("old", encoding="utf-8")
    (install_dir / "data").mkdir()
    (install_dir / "data" / "learnkit.db").write_text("user db", encoding="utf-8")
    (install_dir / "logs").mkdir()
    (install_dir / "logs" / "learnkit.log").write_text("user log", encoding="utf-8")
    (install_dir / "app").mkdir()
    (install_dir / "app" / "logs").mkdir()
    (install_dir / "app" / "logs" / "learnkit.log").write_text("app log", encoding="utf-8")
    package = tmp_path / "release.zip"
    sha = _make_zip(
        package,
        {
            "LearnKit.exe": b"new exe",
            "_internal/new.txt": b"new",
            "data/learnkit.db": b"release must not replace user data",
            "logs/learnkit.log": b"release must not replace logs",
            "app/logs/learnkit.log": b"release must not replace app logs",
            "manifest.json": b"{}",
        },
    )

    install_update(
        package_path=package,
        install_dir=install_dir,
        expected_sha256=sha,
        app_exe=None,
        pid=None,
        restart=False,
    )

    assert (install_dir / "LearnKit.exe").read_bytes() == b"new exe"
    assert (install_dir / "_internal" / "new.txt").read_bytes() == b"new"
    assert (install_dir / "data" / "learnkit.db").read_text(encoding="utf-8") == "user db"
    assert (install_dir / "logs" / "learnkit.log").read_text(encoding="utf-8") == "user log"
    assert (install_dir / "app" / "logs" / "learnkit.log").read_text(encoding="utf-8") == "app log"
    assert list((install_dir / ".learnkit_update_backup").iterdir())


def test_install_update_aborts_before_changes_when_hash_is_invalid(tmp_path) -> None:
    install_dir = tmp_path / "install"
    install_dir.mkdir()
    (install_dir / "LearnKit.exe").write_bytes(b"old exe")
    package = tmp_path / "release.zip"
    _make_zip(package, {"LearnKit.exe": b"new exe"})

    with pytest.raises(UpdateInstallError, match="SHA-256"):
        install_update(
            package_path=package,
            install_dir=install_dir,
            expected_sha256="0" * 64,
            app_exe=None,
            pid=None,
            restart=False,
        )

    assert (install_dir / "LearnKit.exe").read_bytes() == b"old exe"
