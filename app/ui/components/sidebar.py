from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QToolButton, QVBoxLayout, QWidget

from app.version import __version__
from app.ui.components.icons import LineIcon, LogoMark
from app.ui.feedback import future_action, log_action
from app.ui.navigation import NAV_ITEMS, NavItem, visible_nav_items
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
        color = COLORS["accent_hover"] if active else COLORS["muted"]
        text_color = COLORS["text"] if active else COLORS["muted"]
        self.icon.set_color(color)
        self.text.setStyleSheet(f"color: {text_color}; font-size: 15px; font-weight: 650;")
        self.style().unpolish(self)
        self.style().polish(self)

    def set_collapsed(self, collapsed: bool) -> None:
        self.text.setVisible(not collapsed)
        self.setToolTip(self.item.label if collapsed else "")

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
            f"QToolButton {{ background: transparent; border: 1px solid {COLORS['border']}; "
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

    def __init__(self, developer_mode: bool = False) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(260)
        self.items: dict[str, SidebarItem] = {}
        self.collapsed = False
        self.developer_mode = developer_mode

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 26, 14, 16)
        layout.setSpacing(10)

        brand = QHBoxLayout()
        brand.setSpacing(14)
        self.logo = LogoMark(52)
        brand.addWidget(self.logo)
        self.name = QLabel("LearnKit")
        self.name.setStyleSheet("font-size: 24px; font-weight: 820;")
        brand.addWidget(self.name)
        brand.addStretch()
        self.collapse_button = QToolButton()
        self.collapse_button.setObjectName("SidebarCollapseButton")
        self.collapse_button.setFixedSize(34, 34)
        self.collapse_button.setText("<")
        self.collapse_button.setToolTip("Recolher sidebar")
        self.collapse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.collapse_button.clicked.connect(self.toggle_collapsed)
        brand.addWidget(self.collapse_button)
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
        self.community = CollapsibleCommunity()
        layout.addWidget(self.community)
        layout.addSpacing(10)
        self.footer = QLabel(f"Feito com código aberto\nv{__version__}")
        self.footer.setObjectName("Weak")
        self.footer.setWordWrap(True)
        self.footer.setStyleSheet(f"color: {COLORS['weak']}; font-size: 12px;")
        layout.addWidget(self.footer)
        self.set_developer_mode(developer_mode)
        self.set_active("home")

    def set_developer_mode(self, enabled: bool) -> None:
        self.developer_mode = enabled
        for item in NAV_ITEMS:
            button = self.items.get(item.key)
            if button is not None:
                button.setVisible(enabled or not item.developer_only)
        if not enabled and "database" in self.items:
            self.items["database"].set_active(False)

    def visible_item_keys(self) -> list[str]:
        return [item.key for item in visible_nav_items(self.developer_mode)]

    def set_active(self, key: str) -> None:
        for item_key, button in self.items.items():
            button.set_active(item_key == key)

    def toggle_collapsed(self) -> None:
        self.collapsed = not self.collapsed
        self.setFixedWidth(88 if self.collapsed else 260)
        self.logo.setVisible(not self.collapsed)
        self.name.setVisible(not self.collapsed)
        self.community.setVisible(not self.collapsed)
        self.footer.setVisible(not self.collapsed)
        self.collapse_button.setText(">" if self.collapsed else "<")
        self.collapse_button.setToolTip("Expandir sidebar" if self.collapsed else "Recolher sidebar")
        for item in self.items.values():
            item.set_collapsed(self.collapsed)
        log_action("sidebar_collapsed", collapsed=self.collapsed)
