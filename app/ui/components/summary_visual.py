from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.components.cards import EmptyState, label
from app.ui.components.visual import GlassPanel
from app.ui.theme import COLORS


class VisualSummaryWidget(QWidget):
    def __init__(self, summary_visual: str, presentation: bool = False) -> None:
        super().__init__()
        self.summary_visual = summary_visual
        self.presentation = presentation
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        self.layout = QVBoxLayout(content)
        margins = 34 if presentation else 18
        self.layout.setContentsMargins(margins, margins, margins, margins)
        self.layout.setSpacing(18 if presentation else 14)
        scroll.setWidget(content)
        root.addWidget(scroll)
        self._render()

    def _render(self) -> None:
        data = self._parse()
        if data is None:
            self.layout.addWidget(
                EmptyState(
                    "Resumo visual indisponível.",
                    "Este bloco ainda não possui resumo visual válido. Use o modo Texto como fallback.",
                )
            )
            return

        title = str(data.get("title") or "Resumo visual")
        subtitle = str(data.get("subtitle") or "")
        hero = GlassPanel()
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 22, 24, 22)
        title_label = label(title, "HeroTitle")
        title_label.setStyleSheet(
            f"font-size: {34 if self.presentation else 26}px; font-weight: 850;"
        )
        hero_layout.addWidget(title_label)
        if subtitle:
            hero_layout.addWidget(label(subtitle, "Muted"))
        self.layout.addWidget(hero)

        for section in data.get("sections", []):
            if isinstance(section, dict):
                self.layout.addWidget(self._section(section))
        self.layout.addStretch()

    def _parse(self) -> dict[str, Any] | None:
        try:
            parsed = json.loads(self.summary_visual or "{}")
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def _section(self, section: dict[str, Any]) -> QWidget:
        section_type = str(section.get("type") or "section").lower()
        if section_type in {"cards", "key_points"}:
            return self._cards_section(section)
        if section_type == "table":
            return self._table_section(section)
        if section_type in {"steps", "timeline", "checklist"}:
            return self._list_section(section, numbered=section_type == "steps")
        if section_type in {"callout", "warning", "example", "quote", "formula"}:
            return self._callout_section(section)
        if section_type in {"tags"}:
            return self._tags_section(section)
        return self._text_section(section)

    def _text_section(self, section: dict[str, Any]) -> QWidget:
        panel = GlassPanel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)
        title = str(section.get("title") or "Seção")
        text = str(section.get("text") or section.get("content") or "")
        layout.addWidget(label(title, "SectionTitle"))
        if text:
            body = label(text, "Muted")
            body.setStyleSheet(f"font-size: {18 if self.presentation else 14}px; line-height: 1.35;")
            layout.addWidget(body)
        return panel

    def _cards_section(self, section: dict[str, Any]) -> QWidget:
        panel = GlassPanel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        layout.addWidget(label(str(section.get("title") or "Cards"), "SectionTitle"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        items = section.get("items") or []
        for index, item in enumerate(items if isinstance(items, list) else []):
            if not isinstance(item, dict):
                continue
            card = GlassPanel("FeatureCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.addWidget(label(str(item.get("title") or f"Item {index + 1}"), "SmallTitle"))
            card_layout.addWidget(label(str(item.get("text") or ""), "Muted"))
            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid)
        return panel

    def _callout_section(self, section: dict[str, Any]) -> QWidget:
        variant = str(section.get("variant") or section.get("type") or "info").lower()
        color = {
            "warning": COLORS["amber"],
            "example": COLORS["green"],
            "quote": COLORS["purple_soft"],
            "formula": COLORS["blue"],
        }.get(variant, COLORS["blue"])
        panel = GlassPanel()
        panel.setStyleSheet(
            f"QFrame#Panel {{ border: 1px solid {color}; border-radius: 16px; "
            f"background: rgba(11, 22, 38, 0.88); }}"
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.addWidget(label(str(section.get("title") or "Destaque"), "SectionTitle"))
        layout.addWidget(label(str(section.get("text") or ""), "Muted"))
        return panel

    def _table_section(self, section: dict[str, Any]) -> QWidget:
        panel = GlassPanel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)
        layout.addWidget(label(str(section.get("title") or "Tabela"), "SectionTitle"))
        columns = section.get("columns") if isinstance(section.get("columns"), list) else []
        rows = section.get("rows") if isinstance(section.get("rows"), list) else []
        table = QTableWidget(len(rows), len(columns))
        table.setHorizontalHeaderLabels([str(column) for column in columns])
        table.verticalHeader().hide()
        for row_index, row in enumerate(rows):
            values = row if isinstance(row, list) else []
            for column_index, value in enumerate(values[: len(columns)]):
                table.setItem(row_index, column_index, QTableWidgetItem(str(value)))
        table.resizeColumnsToContents()
        table.setMinimumHeight(min(320, 74 + len(rows) * 38))
        layout.addWidget(table)
        return panel

    def _list_section(self, section: dict[str, Any], numbered: bool = False) -> QWidget:
        panel = GlassPanel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)
        layout.addWidget(label(str(section.get("title") or "Lista"), "SectionTitle"))
        items = section.get("items") if isinstance(section.get("items"), list) else []
        for index, item in enumerate(items, start=1):
            prefix = f"{index}." if numbered else "•"
            layout.addWidget(label(f"{prefix} {item}", "Muted"))
        return panel

    def _tags_section(self, section: dict[str, Any]) -> QWidget:
        panel = GlassPanel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.addWidget(label(str(section.get("title") or "Tags"), "SectionTitle"))
        row = QHBoxLayout()
        for item in section.get("items", []):
            tag = QLabel(str(item))
            tag.setStyleSheet(
                f"background: rgba(124, 58, 237, 0.20); border: 1px solid {COLORS['border']}; "
                f"border-radius: 12px; padding: 7px 12px; color: {COLORS['text']};"
            )
            row.addWidget(tag)
        row.addStretch()
        layout.addLayout(row)
        return panel


class PresentationDialog(QDialog):
    def __init__(self, title: str, summary_visual: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Apresentação - {title}")
        self.data = self._parse(summary_visual)
        self.index = 0
        self.sections = self.data.get("sections", []) if self.data else []
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(18, 18, 18, 18)
        self.header = QHBoxLayout()
        self.counter = label("", "Muted")
        close = QPushButton("Sair da apresentação")
        close.clicked.connect(self.accept)
        self.header.addWidget(label(title, "Title"))
        self.header.addStretch()
        self.header.addWidget(self.counter)
        self.header.addWidget(close)
        self.root.addLayout(self.header)
        self.body = QVBoxLayout()
        self.root.addLayout(self.body, 1)
        actions = QHBoxLayout()
        previous = QPushButton("Anterior")
        next_button = QPushButton("Próxima")
        previous.clicked.connect(self.previous)
        next_button.clicked.connect(self.next)
        actions.addStretch()
        actions.addWidget(previous)
        actions.addWidget(next_button)
        self.root.addLayout(actions)
        self.render()

    def _parse(self, raw: str) -> dict[str, Any] | None:
        try:
            value = json.loads(raw or "{}")
        except json.JSONDecodeError:
            return None
        return value if isinstance(value, dict) else None

    def render(self) -> None:
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self.data or not self.sections:
            self.body.addWidget(EmptyState("Sem slides visuais.", "Este bloco não possui seções visuais válidas."))
            return
        section = self.sections[self.index]
        slide_data = {
            "title": str(section.get("title") or self.data.get("title") or "Resumo visual"),
            "subtitle": str(self.data.get("subtitle") or ""),
            "sections": [section],
        }
        self.body.addWidget(VisualSummaryWidget(json.dumps(slide_data, ensure_ascii=False), presentation=True), 1)
        self.counter.setText(f"{self.index + 1} / {len(self.sections)}")

    def next(self) -> None:
        if self.sections:
            self.index = min(self.index + 1, len(self.sections) - 1)
            self.render()

    def previous(self) -> None:
        if self.sections:
            self.index = max(self.index - 1, 0)
            self.render()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        if event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Down, Qt.Key.Key_Space):
            self.next()
            return
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Up, Qt.Key.Key_Backspace):
            self.previous()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
            return
        super().keyPressEvent(event)
