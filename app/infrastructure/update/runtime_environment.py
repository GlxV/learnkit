from __future__ import annotations

import sys
from pathlib import Path


def is_packaged() -> bool:
    return bool(getattr(sys, "frozen", False))


def is_windows() -> bool:
    return sys.platform.startswith("win")


def install_dir() -> Path:
    if is_packaged():
        return Path(sys.executable).resolve().parent
    return Path.cwd().resolve()


def app_executable_name() -> str:
    return "LearnKit.exe" if is_windows() else "LearnKit"


def updater_executable_name() -> str:
    return "LearnKitUpdater.exe" if is_windows() else "LearnKitUpdater"
