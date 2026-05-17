from __future__ import annotations

import ctypes
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path


PROTECTED_ROOTS = {"data", "backups", "logs", ".learnkit_update_backup"}
PROTECTED_PREFIXES = {("app", "logs")}


class UpdateInstallError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_extract_zip(package_path: Path, staging_dir: Path) -> Path:
    staging_dir.mkdir(parents=True, exist_ok=True)
    base = staging_dir.resolve()
    try:
        with zipfile.ZipFile(package_path) as archive:
            for member in archive.infolist():
                target = (base / member.filename).resolve()
                if target != base and base not in target.parents:
                    raise UpdateInstallError(f"Blocked unsafe zip path: {member.filename}")
            archive.extractall(base)
    except zipfile.BadZipFile as exc:
        raise UpdateInstallError(f"Invalid update package: {exc}") from exc
    return base


def install_update(
    package_path: Path,
    install_dir: Path,
    expected_sha256: str,
    app_exe: Path | None,
    pid: int | None = None,
    restart: bool = False,
) -> None:
    package_path = Path(package_path).resolve()
    install_dir = Path(install_dir).resolve()
    if expected_sha256 and sha256_file(package_path).lower() != expected_sha256.lower():
        raise UpdateInstallError("SHA-256 mismatch. Update was not applied.")

    if pid:
        wait_for_process_exit(pid)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_root = Path(tempfile.gettempdir()) / "LearnKit" / "staging" / timestamp
    staging_dir = work_root / "extract"
    backup_dir = install_dir / ".learnkit_update_backup" / timestamp
    try:
        payload_root = find_payload_root(safe_extract_zip(package_path, staging_dir))
        backup_installation(install_dir, backup_dir)
        apply_update(payload_root, install_dir)
    except Exception as exc:  # noqa: BLE001
        rollback(backup_dir, install_dir)
        raise UpdateInstallError(f"Update failed and rollback was attempted: {exc}") from exc
    finally:
        shutil.rmtree(work_root, ignore_errors=True)

    if restart and app_exe is not None:
        subprocess.Popen([str(app_exe)], cwd=str(install_dir))  # noqa: S603


def wait_for_process_exit(pid: int, timeout_seconds: int = 120) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not is_process_running(pid):
            return
        time.sleep(0.5)
    raise UpdateInstallError(f"Timed out waiting for process {pid} to exit.")


def is_process_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform.startswith("win"):
        process_query_limited_information = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(  # type: ignore[attr-defined]
            process_query_limited_information,
            False,
            pid,
        )
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)  # type: ignore[attr-defined]
        return True
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def find_payload_root(staging_dir: Path) -> Path:
    if (staging_dir / "LearnKit.exe").exists() or (staging_dir / "manifest.json").exists():
        return staging_dir
    children = [path for path in staging_dir.iterdir() if path.is_dir()]
    if len(children) == 1:
        return children[0]
    return staging_dir


def backup_installation(install_dir: Path, backup_dir: Path) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    for item in install_dir.rglob("*"):
        relative = item.relative_to(install_dir)
        if should_preserve(relative):
            continue
        target = backup_dir / relative
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def apply_update(payload_root: Path, install_dir: Path) -> None:
    install_dir.mkdir(parents=True, exist_ok=True)
    for item in payload_root.rglob("*"):
        relative = item.relative_to(payload_root)
        if should_preserve(relative):
            continue
        target = install_dir / relative
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def rollback(backup_dir: Path, install_dir: Path) -> None:
    if not backup_dir.exists():
        return
    for item in backup_dir.rglob("*"):
        relative = item.relative_to(backup_dir)
        if should_preserve(relative):
            continue
        target = install_dir / relative
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def should_preserve(relative_path: Path) -> bool:
    parts = tuple(part.lower() for part in relative_path.parts)
    if not parts:
        return False
    if parts[0] in PROTECTED_ROOTS:
        return True
    return any(parts[: len(prefix)] == prefix for prefix in PROTECTED_PREFIXES)
