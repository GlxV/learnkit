from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QWidget

from app.application.dto.update_info import (
    UPDATE_STATUS_AVAILABLE,
    UPDATE_STATUS_DEV_UNAVAILABLE,
    UPDATE_STATUS_ERROR,
    UPDATE_STATUS_MANUAL_ONLY,
    UPDATE_STATUS_UP_TO_DATE,
    DownloadedUpdateDTO,
    UpdateInfoDTO,
)
from app.application.use_cases.check_for_updates import CheckForUpdatesUseCase
from app.application.use_cases.download_update import DownloadUpdateUseCase
from app.infrastructure.update.runtime_environment import (
    app_executable_name,
    install_dir,
    is_packaged,
    updater_executable_name,
)
from app.ui.components.update_dialog import UpdateDialog
from app.ui.feedback import log_action


class UpdateCheckWorker(QObject):
    finished = Signal(object)

    def run(self) -> None:
        info = CheckForUpdatesUseCase().execute()
        self.finished.emit(info)


class UpdateDownloadWorker(QObject):
    progress = Signal(object, object, object)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, update_info: UpdateInfoDTO) -> None:
        super().__init__()
        self.update_info = update_info

    def run(self) -> None:
        try:
            downloaded = DownloadUpdateUseCase().execute(
                self.update_info,
                progress_callback=lambda done, total, percent: self.progress.emit(
                    done,
                    total,
                    percent,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
            return
        self.finished.emit(downloaded)


class UpdateController(QObject):
    def __init__(self, window: QWidget, settings_page: object | None = None) -> None:
        super().__init__(window)
        self.window = window
        self.settings_page = settings_page
        self._check_thread: QThread | None = None
        self._check_worker: UpdateCheckWorker | None = None
        self._download_thread: QThread | None = None
        self._download_worker: UpdateDownloadWorker | None = None
        self._dialog: UpdateDialog | None = None
        self._startup_check_done = False

        if settings_page is not None:
            settings_page.update_check_requested.connect(self.check_manually)
            settings_page.open_releases_requested.connect(self.open_releases)

    def check_on_startup(self) -> None:
        if self._startup_check_done:
            return
        self._startup_check_done = True
        if not is_packaged():
            log_action("update_startup_skipped", reason="dev_mode")
            return
        self._start_check(manual=False)

    def check_manually(self) -> None:
        self._start_check(manual=True)

    def open_releases(self) -> None:
        QDesktopServices.openUrl(QUrl("https://github.com/GlxV/learnkit/releases"))

    def _start_check(self, manual: bool) -> None:
        if self._check_thread is not None:
            self._show_toast("Update check already running.", "info")
            return
        if manual:
            self._set_settings_check_running(True)
            self._set_settings_status("Checking GitHub Releases...")

        thread = QThread(self)
        worker = UpdateCheckWorker()
        self._check_worker = worker
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(lambda info: self._handle_check_result(info, manual))
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._clear_check_thread(manual))
        self._check_thread = thread
        thread.start()

    def _handle_check_result(self, info: UpdateInfoDTO, manual: bool) -> None:
        log_action("update_check_finished", status=info.status, latest=info.latest_version)
        if manual:
            self._set_settings_status(self._status_text(info))

        if info.status == UPDATE_STATUS_AVAILABLE and info.can_auto_update:
            self._show_dialog(info)
            return
        if info.status == UPDATE_STATUS_MANUAL_ONLY and manual:
            self._show_dialog(info)
            return
        if manual and info.status == UPDATE_STATUS_UP_TO_DATE:
            self._show_toast("LearnKit is up to date.", "success")
        elif manual and info.status == UPDATE_STATUS_DEV_UNAVAILABLE:
            self._show_toast(info.reason, "info")
        elif manual and info.status == UPDATE_STATUS_ERROR:
            self._show_toast(f"Could not check updates: {info.reason}", "warning")

    def _show_dialog(self, info: UpdateInfoDTO) -> None:
        if self._dialog is not None:
            self._dialog.close()
        dialog = UpdateDialog(info, self.window)
        dialog.update_now_requested.connect(lambda: self._start_download(info))
        dialog.open_release_requested.connect(lambda: self._open_release(info.release_url))
        self._dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _start_download(self, info: UpdateInfoDTO) -> None:
        if self._download_thread is not None:
            return
        if self._dialog is not None:
            self._dialog.set_downloading()

        thread = QThread(self)
        worker = UpdateDownloadWorker(info)
        self._download_worker = worker
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._handle_download_progress)
        worker.finished.connect(self._handle_download_finished)
        worker.failed.connect(self._handle_download_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_download_thread)
        self._download_thread = thread
        thread.start()

    def _handle_download_progress(
        self,
        downloaded: int,
        total: int | None,
        percent: int | None,
    ) -> None:
        if self._dialog is not None:
            self._dialog.set_progress(downloaded, total, percent)

    def _handle_download_finished(self, downloaded: DownloadedUpdateDTO) -> None:
        log_action("update_download_verified", version=downloaded.version, path=downloaded.package_path)
        if self._dialog is not None:
            self._dialog.set_installing()
        try:
            self._launch_updater(downloaded)
        except Exception as exc:  # noqa: BLE001
            message = f"Could not start updater: {exc}"
            log_action("update_launch_failed", error=exc)
            if self._dialog is not None:
                self._dialog.set_error(message)
            self._show_toast(message, "warning")

    def _handle_download_failed(self, message: str) -> None:
        log_action("update_download_failed", error=message)
        if self._dialog is not None:
            self._dialog.set_error(message)
        self._show_toast(f"Update download failed: {message}", "warning")

    def _launch_updater(self, downloaded: DownloadedUpdateDTO) -> None:
        if not is_packaged():
            raise RuntimeError("Automatic update is only available in packaged builds.")
        current_install_dir = install_dir()
        source_updater = current_install_dir / updater_executable_name()
        if not source_updater.exists():
            raise RuntimeError(f"Updater executable not found: {source_updater}")
        temp_updater_dir = Path(tempfile.gettempdir()) / "LearnKit" / "updater"
        temp_updater_dir.mkdir(parents=True, exist_ok=True)
        temp_updater = temp_updater_dir / updater_executable_name()
        shutil.copy2(source_updater, temp_updater)
        app_exe = current_install_dir / app_executable_name()
        args = [
            str(temp_updater),
            "--package",
            str(downloaded.package_path),
            "--install-dir",
            str(current_install_dir),
            "--app-exe",
            str(app_exe),
            "--pid",
            str(os.getpid()),
            "--expected-sha256",
            downloaded.sha256,
            "--restart",
        ]
        subprocess.Popen(args, cwd=str(current_install_dir))  # noqa: S603
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _open_release(self, release_url: str) -> None:
        QDesktopServices.openUrl(QUrl(release_url or "https://github.com/GlxV/learnkit/releases"))

    def _clear_check_thread(self, manual: bool) -> None:
        self._check_thread = None
        self._check_worker = None
        if manual:
            self._set_settings_check_running(False)

    def _clear_download_thread(self) -> None:
        self._download_thread = None
        self._download_worker = None

    def _set_settings_status(self, text: str) -> None:
        if self.settings_page is not None and hasattr(self.settings_page, "set_update_status"):
            self.settings_page.set_update_status(text)

    def _set_settings_check_running(self, running: bool) -> None:
        if self.settings_page is not None and hasattr(self.settings_page, "set_update_check_running"):
            self.settings_page.set_update_check_running(running)

    def _status_text(self, info: UpdateInfoDTO) -> str:
        if info.status == UPDATE_STATUS_AVAILABLE:
            return f"Version {info.latest_version} is available."
        if info.status == UPDATE_STATUS_MANUAL_ONLY:
            return f"Version {info.latest_version} is available for manual install."
        if info.status == UPDATE_STATUS_UP_TO_DATE:
            return f"LearnKit is up to date ({info.current_version})."
        if info.status == UPDATE_STATUS_DEV_UNAVAILABLE:
            return info.reason
        if info.status == UPDATE_STATUS_ERROR:
            return f"Could not check updates: {info.reason}"
        return info.reason or info.status

    def _show_toast(self, message: str, kind: str = "info") -> None:
        if hasattr(self.window, "show_toast"):
            self.window.show_toast(message, kind)
