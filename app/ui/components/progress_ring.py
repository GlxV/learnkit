from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QConicalGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget

from app.ui.theme import COLORS


class ProgressRing(QWidget):
    def __init__(self, value: int, size: int = 78) -> None:
        super().__init__()
        self.value = max(0, min(100, value))
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(7, 7, -7, -7)
        base_pen = QPen(QColor(COLORS["border"]), 7)
        base_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(base_pen)
        painter.drawArc(rect, 0, 360 * 16)

        gradient = QConicalGradient(self.rect().center(), -90)
        gradient.setColorAt(0.0, QColor(COLORS["purple_soft"]))
        gradient.setColorAt(0.45, QColor(COLORS["blue"]))
        gradient.setColorAt(1.0, QColor(COLORS["purple_soft"]))
        progress_pen = QPen(gradient, 7)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)
        painter.drawArc(rect, 90 * 16, int(-360 * 16 * (self.value / 100)))

        painter.setPen(QColor(COLORS["text"]))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.value}%")
