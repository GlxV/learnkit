from __future__ import annotations

import json
import math
from typing import Any

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QKeyEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
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

from app.application.dto.visual_summary import (
    parse_visual_summary,
    visual_summary_slides,
)
from app.ui.components.cards import EmptyState, label
from app.ui.theme import COLORS


def _panel(elevated: bool = False, accent: str | None = None) -> QFrame:
    panel = QFrame()
    panel.setObjectName("VisualPanel")
    border = accent or COLORS["border"]
    background = COLORS["card_alt"] if elevated else COLORS["card"]
    panel.setStyleSheet(
        f"""
        QFrame#VisualPanel {{
            background: {background};
            border: 1px solid {border};
            border-radius: 14px;
        }}
        """
    )
    return panel


def _body(text: str, size: int = 14, color: str | None = None) -> QLabel:
    widget = label(text, "Muted")
    widget.setWordWrap(True)
    widget.setStyleSheet(
        f"color: {color or COLORS['muted']}; font-size: {size}px; line-height: 1.35;"
    )
    return widget


def _title(text: str, kind: str = "SectionTitle", size: int | None = None) -> QLabel:
    widget = label(text, kind)
    widget.setWordWrap(True)
    if size is not None:
        widget.setStyleSheet(f"font-size: {size}px; font-weight: 800; color: {COLORS['text']};")
    return widget


class ChartWidget(QWidget):
    def __init__(self, block: dict[str, Any], presentation: bool = False) -> None:
        super().__init__()
        self.block = block
        self.presentation = presentation
        self.setMinimumHeight(340 if presentation else 230)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())

    def sizeHint(self) -> QSize:  # type: ignore[override]
        return QSize(780, 360 if self.presentation else 240)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(COLORS["card"]))
        labels = [str(item) for item in self.block.get("labels", [])]
        values = [float(item) for item in self.block.get("values", [])]
        chart_type = str(self.block.get("chart_type") or "bar")
        if not values:
            self._draw_empty(painter)
            return
        if chart_type == "horizontal_bar":
            self._draw_horizontal_bars(painter, labels, values)
        elif chart_type in {"donut", "ring"}:
            self._draw_donut(painter, labels, values)
        elif chart_type == "progress":
            self._draw_progress(painter, labels, values)
        else:
            self._draw_bars(painter, labels, values)

    def _draw_empty(self, painter: QPainter) -> None:
        painter.setPen(QColor(COLORS["muted"]))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Grafico sem dados suficientes.")

    def _draw_bars(self, painter: QPainter, labels: list[str], values: list[float]) -> None:
        rect = self.rect().adjusted(26, 18, -26, -34)
        maximum = max(values) or 1
        count = len(values)
        gap = 14
        bar_width = max(16, int((rect.width() - gap * (count - 1)) / max(count, 1)))
        accent = QColor(COLORS["accent"])
        muted = QColor(COLORS["muted"])
        painter.setPen(Qt.PenStyle.NoPen)
        for index, value in enumerate(values):
            ratio = max(0.0, min(1.0, value / maximum))
            height = max(6, int(rect.height() * ratio))
            x = rect.left() + index * (bar_width + gap)
            y = rect.bottom() - height
            bar = QRectF(x, y, bar_width, height)
            painter.setBrush(accent if index % 2 == 0 else QColor(COLORS["accent_active"]))
            painter.drawRoundedRect(bar, 7, 7)
            painter.setPen(muted)
            painter.drawText(QRectF(x - 8, rect.bottom() + 6, bar_width + 16, 24), Qt.AlignmentFlag.AlignCenter, self._label(labels, index))
            painter.setPen(QColor(COLORS["text"]))
            painter.drawText(QRectF(x - 8, y - 22, bar_width + 16, 18), Qt.AlignmentFlag.AlignCenter, self._format_value(value))
            painter.setPen(Qt.PenStyle.NoPen)

    def _draw_horizontal_bars(self, painter: QPainter, labels: list[str], values: list[float]) -> None:
        rect = self.rect().adjusted(28, 18, -28, -20)
        maximum = max(values) or 1
        row_height = max(32, min(48, rect.height() // max(len(values), 1)))
        for index, value in enumerate(values):
            y = rect.top() + index * row_height
            label_width = min(150, max(82, rect.width() // 4))
            bar_rect = QRectF(rect.left() + label_width, y + 8, rect.width() - label_width - 70, 14)
            painter.setPen(QColor(COLORS["muted"]))
            painter.drawText(QRectF(rect.left(), y, label_width - 10, row_height), Qt.AlignmentFlag.AlignVCenter, self._label(labels, index))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(COLORS["card_alt"]))
            painter.drawRoundedRect(bar_rect, 7, 7)
            fill = QRectF(bar_rect.left(), bar_rect.top(), bar_rect.width() * max(0, value / maximum), bar_rect.height())
            painter.setBrush(QColor(COLORS["accent"]))
            painter.drawRoundedRect(fill, 7, 7)
            painter.setPen(QColor(COLORS["text"]))
            painter.drawText(QRectF(bar_rect.right() + 12, y, 58, row_height), Qt.AlignmentFlag.AlignVCenter, self._format_value(value))

    def _draw_donut(self, painter: QPainter, labels: list[str], values: list[float]) -> None:
        rect = self.rect().adjusted(24, 20, -24, -20)
        size = min(rect.width(), rect.height()) - 10
        center_x = rect.left() + size / 2
        ring = QRectF(rect.left(), rect.top(), size, size)
        total = sum(max(0, value) for value in values) or 1
        start = 90 * 16
        colors = [QColor(COLORS["accent"]), QColor(COLORS["accent_active"]), QColor(COLORS["warning"]), QColor(COLORS["success"])]
        pen = QPen()
        pen.setWidth(24 if self.presentation else 18)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for index, value in enumerate(values):
            span = int(-360 * 16 * (max(0, value) / total))
            pen.setColor(colors[index % len(colors)])
            painter.setPen(pen)
            painter.drawArc(ring, start, span)
            start += span
        painter.setPen(QColor(COLORS["text"]))
        painter.drawText(ring, Qt.AlignmentFlag.AlignCenter, self._format_value(total))
        legend_x = int(center_x + size / 2 + 34)
        for index, value in enumerate(values[:6]):
            y = rect.top() + index * 28
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(colors[index % len(colors)])
            painter.drawRoundedRect(QRectF(legend_x, y + 8, 12, 12), 3, 3)
            painter.setPen(QColor(COLORS["muted"]))
            painter.drawText(QRectF(legend_x + 20, y, rect.right() - legend_x - 20, 24), Qt.AlignmentFlag.AlignVCenter, f"{self._label(labels, index)} - {self._format_value(value)}")

    def _draw_progress(self, painter: QPainter, labels: list[str], values: list[float]) -> None:
        rect = self.rect().adjusted(28, 22, -28, -22)
        row_height = max(36, min(54, rect.height() // max(len(values), 1)))
        for index, value in enumerate(values):
            y = rect.top() + index * row_height
            progress = max(0.0, min(100.0, value)) / 100
            painter.setPen(QColor(COLORS["muted"]))
            painter.drawText(QRectF(rect.left(), y, rect.width(), 18), Qt.AlignmentFlag.AlignLeft, self._label(labels, index))
            bar = QRectF(rect.left(), y + 24, rect.width() - 64, 12)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(COLORS["card_alt"]))
            painter.drawRoundedRect(bar, 6, 6)
            painter.setBrush(QColor(COLORS["accent"]))
            painter.drawRoundedRect(QRectF(bar.left(), bar.top(), bar.width() * progress, bar.height()), 6, 6)
            painter.setPen(QColor(COLORS["text"]))
            painter.drawText(QRectF(bar.right() + 12, y + 17, 52, 22), Qt.AlignmentFlag.AlignVCenter, f"{int(value)}%")

    def _label(self, labels: list[str], index: int) -> str:
        if index < len(labels) and labels[index]:
            return labels[index]
        return f"Item {index + 1}"

    def _format_value(self, value: float) -> str:
        if math.isclose(value, int(value)):
            return str(int(value))
        return f"{value:.1f}"


class SummaryVisualRenderer:
    def __init__(self, presentation: bool = False) -> None:
        self.presentation = presentation
        self.title_size = 34 if presentation else 26
        self.section_title_size = 25 if presentation else 17
        self.body_size = 18 if presentation else 14

    def render_summary(self, layout: QVBoxLayout, data: dict[str, Any]) -> None:
        sections = data.get("sections") if isinstance(data.get("sections"), list) else []
        if sections and isinstance(sections[0], dict) and sections[0].get("type") == "hero":
            layout.addWidget(self.render_block(sections[0], root_title=data.get("title"), root_subtitle=data.get("subtitle")))
            sections = sections[1:]
        else:
            layout.addWidget(
                self._hero(
                    {
                        "title": data.get("title") or "Resumo visual",
                        "subtitle": data.get("subtitle") or "",
                        "text": "Mapa visual para revisar os pontos principais do bloco.",
                    }
                )
            )
        for section in sections:
            if isinstance(section, dict):
                layout.addWidget(self.render_block(section))

    def render_block(self, block: dict[str, Any], root_title: object | None = None, root_subtitle: object | None = None) -> QWidget:
        block_type = str(block.get("type") or "section")
        if block_type == "hero":
            return self._hero(block, root_title=root_title, root_subtitle=root_subtitle)
        if block_type == "cards":
            return self._cards(block)
        if block_type == "callout":
            return self._callout(block)
        if block_type == "table":
            return self._table(block)
        if block_type == "comparison":
            return self._comparison(block)
        if block_type in {"steps", "timeline", "mistakes"}:
            return self._sequence(block, block_type)
        if block_type == "tags":
            return self._tags(block)
        if block_type in {"formula", "definition", "example"}:
            return self._definition_like(block, block_type)
        if block_type == "flow":
            return self._flow(block)
        if block_type == "chart":
            return self._chart(block)
        return self._section(block)

    def _hero(self, block: dict[str, Any], root_title: object | None = None, root_subtitle: object | None = None) -> QWidget:
        panel = _panel(elevated=True, accent=COLORS["border_hover"])
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(30 if self.presentation else 24, 26 if self.presentation else 20, 30 if self.presentation else 24, 26 if self.presentation else 20)
        layout.setSpacing(12)
        eyebrow = str(root_subtitle or block.get("subtitle") or "").strip()
        if eyebrow:
            tag = QLabel(eyebrow)
            tag.setStyleSheet(
                f"background: {COLORS['accent_dark']}; border: 1px solid {COLORS['border_hover']}; "
                f"border-radius: 12px; padding: 6px 10px; color: {COLORS['text']}; font-weight: 700;"
            )
            tag.setMaximumWidth(520)
            layout.addWidget(tag)
        layout.addWidget(_title(str(block.get("title") or root_title or "Resumo visual"), "HeroTitle", self.title_size))
        text = str(block.get("text") or block.get("content") or "")
        if text:
            layout.addWidget(_body(text, self.body_size))
        return panel

    def _section(self, block: dict[str, Any]) -> QWidget:
        panel = _panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)
        layout.addWidget(_title(str(block.get("title") or "Secao"), "SectionTitle", self.section_title_size))
        text = str(block.get("text") or block.get("content") or "")
        if text:
            layout.addWidget(_body(text, self.body_size))
        return panel

    def _cards(self, block: dict[str, Any]) -> QWidget:
        panel = _panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        layout.addWidget(_title(str(block.get("title") or "Cards"), "SectionTitle", self.section_title_size))
        items = block.get("items") if isinstance(block.get("items"), list) else []
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        columns = 2 if self.presentation or len(items) < 5 else 3
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            card = _panel(elevated=True)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(8)
            card_layout.addWidget(_title(str(item.get("title") or f"Item {index + 1}"), "SmallTitle"))
            if item.get("text"):
                card_layout.addWidget(_body(str(item.get("text")), self.body_size))
            self._add_points(card_layout, item)
            grid.addWidget(card, index // columns, index % columns)
        layout.addLayout(grid)
        return panel

    def _callout(self, block: dict[str, Any]) -> QWidget:
        variant = str(block.get("variant") or "info")
        color = {
            "info": COLORS["accent"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "danger": COLORS["error"],
            "tip": COLORS["accent_hover"],
            "example": COLORS["success"],
            "formula": COLORS["accent"],
        }.get(variant, COLORS["accent"])
        panel = _panel(elevated=True, accent=color)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(8)
        layout.addWidget(_title(str(block.get("title") or "Destaque"), "SectionTitle", self.section_title_size))
        text = str(block.get("text") or "")
        if text:
            layout.addWidget(_body(text, self.body_size))
        self._add_item_list(layout, block)
        return panel

    def _table(self, block: dict[str, Any]) -> QWidget:
        panel = _panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)
        layout.addWidget(_title(str(block.get("title") or "Tabela"), "SectionTitle", self.section_title_size))
        headers = block.get("headers") if isinstance(block.get("headers"), list) else []
        rows = block.get("rows") if isinstance(block.get("rows"), list) else []
        column_count = max(len(headers), max((len(row) for row in rows if isinstance(row, list)), default=0), 1)
        table = QTableWidget(len(rows), column_count)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.verticalHeader().hide()
        table.setHorizontalHeaderLabels([str(headers[index]) if index < len(headers) else "" for index in range(column_count)])
        for row_index, row in enumerate(rows):
            values = row if isinstance(row, list) else []
            for column_index, value in enumerate(values[:column_count]):
                table.setItem(row_index, column_index, QTableWidgetItem(str(value)))
        table.horizontalHeader().setStretchLastSection(True)
        table.resizeRowsToContents()
        table.setMinimumHeight(min(420 if self.presentation else 320, 78 + max(1, len(rows)) * 42))
        layout.addWidget(table)
        return panel

    def _comparison(self, block: dict[str, Any]) -> QWidget:
        panel = _panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        layout.addWidget(_title(str(block.get("title") or "Comparacao"), "SectionTitle", self.section_title_size))
        items = block.get("items") if isinstance(block.get("items"), list) else []
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            card = _panel(elevated=True)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.addWidget(_title(str(item.get("title") or f"Item {index + 1}"), "SmallTitle"))
            if item.get("text"):
                card_layout.addWidget(_body(str(item.get("text")), self.body_size))
            self._add_points(card_layout, item)
            grid.addWidget(card, 0, index)
        layout.addLayout(grid)
        return panel

    def _sequence(self, block: dict[str, Any], block_type: str) -> QWidget:
        title_map = {"steps": "Passos", "timeline": "Linha do tempo", "mistakes": "Erros comuns"}
        panel = _panel(accent=COLORS["warning"] if block_type == "mistakes" else None)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)
        layout.addWidget(_title(str(block.get("title") or title_map[block_type]), "SectionTitle", self.section_title_size))
        items = block.get("items") if isinstance(block.get("items"), list) else []
        for index, item in enumerate(items, start=1):
            row = QHBoxLayout()
            item_data = item if isinstance(item, dict) else {"title": str(item), "text": "", "number": str(index)}
            badge_text = "!" if block_type == "mistakes" else str(item_data.get("number") or index)
            badge = QLabel(badge_text)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFixedSize(30, 30)
            badge.setStyleSheet(
                f"background: {COLORS['accent_dark']}; border: 1px solid {COLORS['border_hover']}; "
                f"border-radius: 15px; color: {COLORS['text']}; font-weight: 800;"
            )
            row.addWidget(badge)
            content = QVBoxLayout()
            content.setSpacing(4)
            title = str(item_data.get("title") or "")
            text = str(item_data.get("text") or "")
            if title:
                content.addWidget(_title(title, "SmallTitle"))
            if text:
                content.addWidget(_body(text, self.body_size))
            if not title and not text:
                content.addWidget(_body(str(item), self.body_size))
            row.addLayout(content, 1)
            layout.addLayout(row)
        return panel

    def _tags(self, block: dict[str, Any]) -> QWidget:
        panel = _panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)
        layout.addWidget(_title(str(block.get("title") or "Tags"), "SectionTitle", self.section_title_size))
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        items = block.get("items") if isinstance(block.get("items"), list) else []
        columns = 4 if not self.presentation else 3
        for index, item in enumerate(items):
            tag = QLabel(str(item))
            tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tag.setStyleSheet(
                f"background: {COLORS['accent_dark']}; border: 1px solid {COLORS['border']}; "
                f"border-radius: 13px; padding: 7px 12px; color: {COLORS['text']}; font-weight: 650;"
            )
            grid.addWidget(tag, index // columns, index % columns)
        layout.addLayout(grid)
        return panel

    def _definition_like(self, block: dict[str, Any], block_type: str) -> QWidget:
        title = str(block.get("title") or {"formula": "Formula", "definition": "Definicao", "example": "Exemplo"}[block_type])
        text = str(block.get("text") or block.get("definition") or block.get("content") or "")
        accent = COLORS["accent"] if block_type != "example" else COLORS["success"]
        panel = _panel(elevated=True, accent=accent)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(8)
        layout.addWidget(_title(title, "SectionTitle", self.section_title_size))
        if text:
            body = _body(text, self.body_size, COLORS["text"] if block_type == "formula" else COLORS["muted"])
            layout.addWidget(body)
        self._add_item_list(layout, block, strong_body=block_type == "formula")
        return panel

    def _flow(self, block: dict[str, Any]) -> QWidget:
        panel = _panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        layout.addWidget(_title(str(block.get("title") or "Fluxo"), "SectionTitle", self.section_title_size))
        row = QHBoxLayout()
        row.setSpacing(8)
        items = block.get("items") if isinstance(block.get("items"), list) else []
        for index, item in enumerate(items):
            pill = QLabel(str(item))
            pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pill.setStyleSheet(
                f"background: {COLORS['card_alt']}; border: 1px solid {COLORS['border_hover']}; "
                f"border-radius: 12px; padding: 9px 12px; color: {COLORS['text']}; font-weight: 700;"
            )
            row.addWidget(pill)
            if index < len(items) - 1:
                arrow = QLabel("->")
                arrow.setStyleSheet(f"color: {COLORS['accent_hover']}; font-weight: 900;")
                row.addWidget(arrow)
        row.addStretch()
        layout.addLayout(row)
        return panel

    def _chart(self, block: dict[str, Any]) -> QWidget:
        panel = _panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)
        layout.addWidget(_title(str(block.get("title") or "Grafico"), "SectionTitle", self.section_title_size))
        description = str(block.get("description") or "")
        if description:
            layout.addWidget(_body(description, self.body_size))
        chart = ChartWidget(block, presentation=self.presentation)
        chart.setStyleSheet(f"background: {COLORS['card']}; border-radius: 12px;")
        layout.addWidget(chart)
        unit = str(block.get("unit") or "")
        if unit:
            layout.addWidget(_body(f"Unidade: {unit}", 12, COLORS["weak"]))
        return panel

    def _add_item_list(self, layout: QVBoxLayout, block: dict[str, Any], strong_body: bool = False) -> None:
        items = block.get("items") if isinstance(block.get("items"), list) else []
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                layout.addWidget(_body(str(item), self.body_size))
                continue
            card = _panel(elevated=True)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(6)
            title = str(item.get("title") or f"Item {index}")
            text = str(item.get("text") or "")
            if title:
                card_layout.addWidget(_title(title, "SmallTitle"))
            if text:
                card_layout.addWidget(
                    _body(text, self.body_size, COLORS["text"] if strong_body else COLORS["muted"])
                )
            self._add_points(card_layout, item)
            layout.addWidget(card)

    def _add_points(self, layout: QVBoxLayout, item: dict[str, Any]) -> None:
        points = item.get("points") if isinstance(item.get("points"), list) else []
        for point in points:
            layout.addWidget(_body(f"- {point}", self.body_size))


class VisualSummaryWidget(QWidget):
    def __init__(self, summary_visual: str, presentation: bool = False) -> None:
        super().__init__()
        self.summary_visual = summary_visual
        self.presentation = presentation
        self.setObjectName("VisualSummaryWidget")
        self.setStyleSheet(f"QWidget#VisualSummaryWidget {{ background: {COLORS['background']}; }}")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setObjectName("VisualSummaryScroll")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setStyleSheet(
            f"QScrollArea#VisualSummaryScroll, QScrollArea#VisualSummaryScroll > QWidget > QWidget {{ background: {COLORS['background']}; border: 0; }}"
        )
        content = QWidget()
        content.setObjectName("VisualSummaryContent")
        content.setStyleSheet(f"QWidget#VisualSummaryContent {{ background: {COLORS['background']}; }}")
        self.layout = QVBoxLayout(content)
        margins = 34 if presentation else 18
        self.layout.setContentsMargins(margins, margins, margins, margins)
        self.layout.setSpacing(20 if presentation else 14)
        scroll.setWidget(content)
        root.addWidget(scroll)
        self._render()

    def _render(self) -> None:
        data = parse_visual_summary(self.summary_visual)
        if data is None:
            self.layout.addWidget(
                EmptyState(
                    "Resumo visual indisponivel.",
                    "Este bloco ainda nao possui resumo visual valido. Use o modo Texto como fallback.",
                )
            )
            self.layout.addStretch()
            return
        SummaryVisualRenderer(self.presentation).render_summary(self.layout, data)
        self.layout.addStretch()


class PresentationDialog(QDialog):
    def __init__(self, title: str, summary_visual: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Apresentacao - {title}")
        self.resize(1220, 820)
        self.setObjectName("PresentationDialog")
        self.setStyleSheet(
            f"""
            QDialog#PresentationDialog {{
                background: {COLORS['background']};
            }}
            """
        )
        self.data = parse_visual_summary(summary_visual)
        self.slides = visual_summary_slides(self.data)
        self.index = 0
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(22, 20, 22, 20)
        self.root.setSpacing(14)

        self.header = QHBoxLayout()
        self.counter = label("", "Muted")
        close = QPushButton("Sair da apresentacao")
        close.clicked.connect(self.accept)
        self.header.addWidget(label(title, "Title"))
        self.header.addStretch()
        self.header.addWidget(self.counter)
        self.header.addWidget(close)
        self.root.addLayout(self.header)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.root.addLayout(self.body, 1)

        actions = QHBoxLayout()
        self.previous_button = QPushButton("Anterior")
        self.next_button = QPushButton("Proxima")
        self.previous_button.clicked.connect(self.previous)
        self.next_button.clicked.connect(self.next)
        actions.addStretch()
        actions.addWidget(self.previous_button)
        actions.addWidget(self.next_button)
        self.root.addLayout(actions)
        self.render()

    def render(self) -> None:
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self.slides:
            self.body.addWidget(EmptyState("Sem slides visuais.", "Este bloco nao possui secoes visuais validas."))
            self.counter.setText("0 / 0")
            return
        slide = self.slides[self.index]
        wrapper = QWidget()
        wrapper.setObjectName("PresentationSlide")
        wrapper.setStyleSheet(f"QWidget#PresentationSlide {{ background: {COLORS['background']}; }}")
        slide_layout = QVBoxLayout(wrapper)
        slide_layout.setContentsMargins(34, 26, 34, 26)
        slide_layout.addStretch(1)
        slide_layout.addWidget(SummaryVisualRenderer(presentation=True).render_block(slide), 4)
        slide_layout.addStretch(1)
        self.body.addWidget(wrapper, 1)
        total = len(self.slides)
        self.counter.setText(f"{self.index + 1} / {total}")
        self.previous_button.setEnabled(self.index > 0)
        self.next_button.setEnabled(self.index < total - 1)

    def next(self) -> None:
        if self.slides:
            self.index = min(self.index + 1, len(self.slides) - 1)
            self.render()

    def previous(self) -> None:
        if self.slides:
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
