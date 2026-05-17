from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.application.dto.update_info import UpdateInfoDTO


class UpdateDialog(QDialog):
    update_now_requested = Signal()
    open_release_requested = Signal()

    def __init__(self, update_info: UpdateInfoDTO, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.update_info = update_info
        self.setWindowTitle("LearnKit update")
        self.resize(560, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("A new LearnKit version is available")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        version = QLabel(
            f"Current version: {update_info.current_version}\n"
            f"New version: {update_info.latest_version}"
        )
        version.setWordWrap(True)
        layout.addWidget(version)

        if update_info.reason:
            reason = QLabel(update_info.reason)
            reason.setWordWrap(True)
            layout.addWidget(reason)

        self.changelog = QPlainTextEdit()
        self.changelog.setReadOnly(True)
        self.changelog.setPlainText(update_info.changelog or "No changelog provided.")
        layout.addWidget(self.changelog, 1)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.hide()
        layout.addWidget(self.progress)

        actions = QHBoxLayout()
        actions.addStretch()
        self.update_later_button = QPushButton("Update later")
        self.open_release_button = QPushButton("Open release")
        self.update_now_button = QPushButton("Update now")
        self.update_now_button.setObjectName("PrimaryButton")
        self.update_now_button.setEnabled(update_info.can_auto_update)
        self.update_later_button.clicked.connect(self.reject)
        self.open_release_button.clicked.connect(self.open_release_requested.emit)
        self.update_now_button.clicked.connect(self.update_now_requested.emit)
        actions.addWidget(self.update_later_button)
        actions.addWidget(self.open_release_button)
        actions.addWidget(self.update_now_button)
        layout.addLayout(actions)

    def set_downloading(self) -> None:
        self.status.setText("Downloading update package...")
        self.progress.show()
        self.progress.setValue(0)
        self.update_now_button.setEnabled(False)
        self.open_release_button.setEnabled(False)

    def set_progress(self, downloaded: int, total: int | None, percent: int | None) -> None:
        if percent is not None:
            self.progress.setRange(0, 100)
            self.progress.setValue(max(0, min(100, percent)))
        else:
            self.progress.setRange(0, 0)
        if total:
            self.status.setText(f"Downloaded {downloaded} of {total} bytes.")
        else:
            self.status.setText(f"Downloaded {downloaded} bytes.")

    def set_error(self, message: str) -> None:
        self.progress.hide()
        self.status.setText(message)
        self.update_now_button.setEnabled(self.update_info.can_auto_update)
        self.open_release_button.setEnabled(True)

    def set_installing(self) -> None:
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.status.setText("Download verified. Starting updater...")
