from __future__ import annotations

import os
import sys

from app.application.dto.update_info import UpdateInfoDTO


def _qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def test_settings_page_exposes_update_actions(tmp_path) -> None:
    _qapp()

    from app.core.database.sqlite_storage import SQLiteStorage
    from app.ui.pages.settings_page import SettingsPage

    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    page = SettingsPage(storage)
    checks: list[bool] = []
    releases: list[bool] = []
    page.update_check_requested.connect(lambda: checks.append(True))
    page.open_releases_requested.connect(lambda: releases.append(True))

    page.check_updates_button.click()
    page.open_releases_button.click()
    page.set_update_check_running(True)

    assert checks == [True]
    assert releases == [True]
    assert page.check_updates_button.isEnabled() is False

    page.set_update_status("Status atualizado")
    page.set_update_check_running(False)

    assert page.update_status.text() == "Status atualizado"
    assert page.check_updates_button.isEnabled() is True


def test_update_dialog_disables_update_now_for_manual_only_release() -> None:
    _qapp()

    from app.ui.components.update_dialog import UpdateDialog

    dialog = UpdateDialog(
        UpdateInfoDTO(
            status="manual_only",
            current_version="0.1.0",
            latest_version="0.2.0",
            release_url="https://github.com/GlxV/learnkit/releases/tag/v0.2.0",
            can_auto_update=False,
            reason="Release without manifest.",
        )
    )

    assert dialog.update_now_button.isEnabled() is False
    assert dialog.open_release_button.isEnabled() is True


def test_update_dialog_enables_update_now_for_installable_release() -> None:
    _qapp()

    from app.ui.components.update_dialog import UpdateDialog

    dialog = UpdateDialog(
        UpdateInfoDTO(
            status="update_available",
            current_version="0.1.0",
            latest_version="0.2.0",
            release_url="https://github.com/GlxV/learnkit/releases/tag/v0.2.0",
            asset_name="LearnKit-0.2.0-win.zip",
            asset_url="https://example.test/LearnKit-0.2.0-win.zip",
            sha256="a" * 64,
            can_auto_update=True,
        )
    )

    assert dialog.update_now_button.isEnabled() is True
