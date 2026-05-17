from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QWidget

from app.ui.components.icons import LineIcon, supports_line_icon
from app.ui.theme import COLORS


def add_shadow(widget: QWidget, blur: int = 28, y_offset: int = 10, alpha: int = 70) -> None:
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, y_offset)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)


class IconBadge(QFrame):
    def __init__(
        self,
        text: str,
        color: str = COLORS["accent"],
        size: int = 46,
        radius: int = 14,
        font_size: int = 17,
    ) -> None:
        super().__init__()
        self._value = text
        self._color = color
        self._size = size
        self._radius = radius
        self._font_size = font_size
        self.setFixedSize(size, size)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content: QWidget | None = None
        self._apply_frame_style()
        self.setText(text)

    def setText(self, text: str) -> None:
        self._value = text
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._content = None

        if supports_line_icon(text):
            icon = LineIcon(text, "#FFFFFF", max(18, int(self._size * 0.54)))
            icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self._content = icon
        else:
            fallback = QLabel(text)
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setStyleSheet(
                f"background: transparent; color: white; "
                f"font-size: {self._font_size}px; font-weight: 850;"
            )
            self._content = fallback
        self._layout.addWidget(self._content)

    def text(self) -> str:
        return self._value

    def set_color(self, color: str) -> None:
        self._color = color
        self._apply_frame_style()

    def setStyleSheet(self, style_sheet: str) -> None:  # type: ignore[override]
        super().setStyleSheet(style_sheet)

    def _apply_frame_style(self) -> None:
        super().setStyleSheet(
            f"""
            QFrame {{
                background: {self._color};
                border-radius: {self._radius}px;
                border: 1px solid rgba(255, 255, 255, 0.16);
            }}
            """
        )


class SoftIconBadge(QLabel):
    def __init__(
        self,
        text: str,
        color: str = COLORS["accent_hover"],
        size: int = 50,
        font_size: int = 18,
    ) -> None:
        super().__init__(text)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"""
            QLabel {{
                background: {COLORS["accent_dark"]};
                border: 1px solid {COLORS["border_hover"]};
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
