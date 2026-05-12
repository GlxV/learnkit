from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QToolButton, QVBoxLayout, QWidget

from app.ui.components.icons import LineIcon, LogoMark
from app.ui.feedback import future_action, log_action
from app.ui.navigation import NAV_ITEMS, NavItem
from app.ui.theme import COLORS


class SidebarItem(QFrame):
    clicked = Signal(str)

    def __init__(self, item: NavItem) -> None:
        super().__init__()
        self.item = item
        self.setObjectName("SidebarItemFrame")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.icon = LineIcon(item.icon, COLORS["muted"], 24)
        self.text = QLabel(item.label)
        self.text.setStyleSheet(f"color: {COLORS['muted']}; font-size: 15px; font-weight: 600;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 11, 14, 11)
        layout.setSpacing(12)
        layout.addWidget(self.icon)
        layout.addWidget(self.text, 1)

    def set_active(self, active: bool) -> None:
        self.setProperty("active", "true" if active else "false")
        color = COLORS["purple_soft"] if active else COLORS["muted"]
        text_color = COLORS["text"] if active else COLORS["muted"]
        self.icon.set_color(color)
        self.text.setStyleSheet(f"color: {text_color}; font-size: 15px; font-weight: 650;")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self.clicked.emit(self.item.key)
        super().mousePressEvent(event)


class CollapsibleCommunity(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.toggle = QToolButton()
        self.toggle.setCheckable(True)
        self.toggle.setStyleSheet(
            "QToolButton { background: transparent; border: 1px solid #1E2A3D; "
            "border-radius: 10px; padding: 10px 12px; text-align: left; "
            f"color: {COLORS['text']}; font-size: 15px; }}"
        )
        self._set_toggle_text(False)
        self.toggle.clicked.connect(self._toggle)
        layout.addWidget(self.toggle)

        self.content = QFrame()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(10, 0, 0, 0)
        content_layout.setSpacing(4)
        for text in ["Feito com codigo aberto", "Ver repositorio", "Contribuir", "Reportar problema"]:
            button = QPushButton(text)
            button.setObjectName("SidebarItem")
            button.setToolTip("Disponivel quando o repositorio publico for configurado.")
            button.clicked.connect(lambda checked=False, feature=text: future_action(self, feature))
            content_layout.addWidget(button)
        self.content.setVisible(False)
        layout.addWidget(self.content)

    def _set_toggle_text(self, expanded: bool) -> None:
        self.toggle.setText("  Comunidade        v" if expanded else "  Comunidade        >")

    def _toggle(self) -> None:
        expanded = self.toggle.isChecked()
        self.content.setVisible(expanded)
        self._set_toggle_text(expanded)
        log_action("community_toggled", expanded=expanded)


class Sidebar(QFrame):
    page_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(260)
        self.items: dict[str, SidebarItem] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 26, 14, 16)
        layout.setSpacing(10)

        brand = QHBoxLayout()
        brand.setSpacing(14)
        brand.addWidget(LogoMark(52))
        name = QLabel("LearnKit")
        name.setStyleSheet("font-size: 24px; font-weight: 820;")
        brand.addWidget(name)
        brand.addStretch()
        layout.addLayout(brand)
        layout.addSpacing(26)

        for item in NAV_ITEMS:
            button = SidebarItem(item)
            button.clicked.connect(self.page_selected.emit)
            self.items[item.key] = button
            layout.addWidget(button)
            if item.key == "settings":
                layout.addSpacing(6)

        layout.addStretch()
        layout.addWidget(CollapsibleCommunity())
        layout.addSpacing(10)
        footer = QLabel("Feito com codigo aberto\nv0.1.0")
        footer.setObjectName("Weak")
        footer.setWordWrap(True)
        footer.setStyleSheet(f"color: {COLORS['weak']}; font-size: 12px;")
        layout.addWidget(footer)
        self.set_active("home")

    def set_active(self, key: str) -> None:
        for item_key, button in self.items.items():
            button.set_active(item_key == key)
