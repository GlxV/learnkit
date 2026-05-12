from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QLabel, QWidget

from app.ui.theme import COLORS


def add_shadow(widget: QWidget, blur: int = 28, y_offset: int = 10, alpha: int = 70) -> None:
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, y_offset)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)


class IconBadge(QLabel):
    def __init__(
        self,
        text: str,
        color: str = COLORS["purple"],
        size: int = 46,
        radius: int = 14,
        font_size: int = 17,
    ) -> None:
        super().__init__(text)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"""
            QLabel {{
                background: {color};
                border-radius: {radius}px;
                color: white;
                font-size: {font_size}px;
                font-weight: 850;
            }}
            """
        )


class SoftIconBadge(QLabel):
    def __init__(
        self,
        text: str,
        color: str = COLORS["purple_soft"],
        size: int = 50,
        font_size: int = 18,
    ) -> None:
        super().__init__(text)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"""
            QLabel {{
                background: rgba(124, 58, 237, 0.20);
                border: 1px solid rgba(139, 92, 246, 0.28);
                border-radius: {size // 2}px;
                color: {color};
                font-size: {font_size}px;
                font-weight: 850;
            }}
            """
        )


class GlassPanel(QFrame):
    def __init__(self, object_name: str = "Panel", shadow: bool = True) -> None:
        super().__init__()
        self.setObjectName(object_name)
        if shadow:
            add_shadow(self)
