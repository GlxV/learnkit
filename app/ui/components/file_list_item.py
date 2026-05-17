from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.ui.theme import COLORS


class FileListItem(QFrame):
    remove_requested = Signal(object)

    def __init__(self, path: Path, status: str = "aguardando", detail: str = "") -> None:
        super().__init__()
        self.path = path
        self.setObjectName("FileListItem")
        self.setToolTip(str(path))
        self.setMinimumHeight(72)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 12, 10)
        layout.setSpacing(12)

        icon = QLabel(self._icon_for(path))
        icon.setFixedSize(42, 42)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(
            f"background: {COLORS['accent_dark']};"
            f"border: 1px solid {COLORS['border_hover']};"
            "border-radius: 12px;"
            "font-weight: 800;"
        )
        layout.addWidget(icon)

        text_box = QVBoxLayout()
        text_box.setSpacing(3)
        name = QLabel(path.name)
        name.setStyleSheet("font-weight: 750;")
        meta = QLabel(f"{path.suffix.upper().lstrip('.') or 'ARQ'} - {self._size_label(path)}")
        meta.setObjectName("Weak")
        text_box.addWidget(name)
        text_box.addWidget(meta)
        if detail:
            detail_label = QLabel(detail)
            detail_label.setObjectName("Weak")
            text_box.addWidget(detail_label)
        layout.addLayout(text_box, 1)

        status_label = QLabel(self._status_label(status))
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet(
            f"color: {self._status_color(status)};"
            "font-weight: 700;"
            "padding: 5px 9px;"
            "border-radius: 9px;"
        )
        layout.addWidget(status_label)

        remove = QPushButton("Remover")
        remove.setObjectName("GhostButton")
        remove.setCursor(Qt.CursorShape.PointingHandCursor)
        remove.clicked.connect(lambda: self.remove_requested.emit(self.path))
        layout.addWidget(remove)

    def _icon_for(self, path: Path) -> str:
        ext = path.suffix.lower()
        if ext == ".pdf":
            return "PDF"
        if ext == ".pptx":
            return "PPT"
        if ext == ".docx":
            return "DOC"
        if ext in {".txt", ".md", ".markdown"}:
            return "TXT"
        return "ARQ"

    def _size_label(self, path: Path) -> str:
        if not path.exists():
            return "arquivo ausente"
        size = path.stat().st_size
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        return f"{size / 1024:.1f} KB"

    def _status_label(self, status: str) -> str:
        return {
            "aguardando": "Aguardando",
            "extraindo": "Extraindo",
            "extraido": "Extraido",
            "aviso": "Aviso",
            "erro": "Erro",
        }.get(status, status.title())

    def _status_color(self, status: str) -> str:
        return {
            "aguardando": COLORS["muted"],
            "extraindo": COLORS["accent"],
            "extraido": COLORS["green"],
            "aviso": COLORS["amber"],
            "erro": COLORS["red"],
        }.get(status, COLORS["muted"])
