from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QWidget

from app.ui.theme import COLORS


class Toast(QFrame):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlags(Qt.WindowType.Widget)
        self.hide()

        self.label = QLabel()
        self.label.setWordWrap(True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.addWidget(self.label)

        self.opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)
        self.animation = QPropertyAnimation(self.opacity, b"opacity", self)
        self.animation.setDuration(180)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._fade_out)

    def show_message(self, message: str, kind: str = "info") -> None:
        self.timer.stop()
        self.animation.stop()
        try:
            self.animation.finished.disconnect(self.hide)
        except RuntimeError:
            pass
        self.label.setText(message)
        self.setStyleSheet(self._style_for(kind))
        self.setMaximumWidth(440)
        self.adjustSize()
        self._reposition()
        self.opacity.setOpacity(0.0)
        self.show()
        self.raise_()
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()
        self.timer.start(3200)

    def reposition(self) -> None:
        if self.isVisible():
            self._reposition()

    def _fade_out(self) -> None:
        self.animation.stop()
        self.animation.setStartValue(self.opacity.opacity())
        self.animation.setEndValue(0.0)
        try:
            self.animation.finished.disconnect(self.hide)
        except RuntimeError:
            pass
        self.animation.finished.connect(self.hide)
        self.animation.start()

    def _reposition(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        margin = 24
        x = max(margin, parent.width() - self.width() - margin)
        y = max(margin, parent.height() - self.height() - margin)
        self.move(x, y)

    def _style_for(self, kind: str) -> str:
        color = {
            "success": COLORS["green"],
            "error": COLORS["red"],
            "warning": COLORS["amber"],
            "info": COLORS["accent"],
        }.get(kind, COLORS["accent"])
        return (
            "QFrame#Toast {"
            f"background: {COLORS['card']};"
            f"border: 1px solid {color};"
            "border-radius: 12px;"
            "}"
            "QLabel {"
            f"color: {COLORS['text']};"
            "font-weight: 600;"
            "}"
        )
