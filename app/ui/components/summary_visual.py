from __future__ import annotations

import json
import math
from typing import Any

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QKeyEvent, QPainter, QPen
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
from app.application.dto.visual_preset import get_visual_preset
from app.ui.components.cards import EmptyState, label
from app.ui.theme import COLORS


def _visual_palette(style: object | None = None) -> dict[str, str]:
    return dict(get_visual_preset(style).palette)


def _panel(
    elevated: bool = False,
    accent: str | None = None,
    background: str | None = None,
    radius: int = 16,
) -> QFrame:
    panel = QFrame()
    panel.setObjectName("VisualPanel")
    border = accent or COLORS["border"]
    selected_background = background or (COLORS["card_alt"] if elevated else COLORS["card"])
    panel.setStyleSheet(
        f"""
        QFrame#VisualPanel {{
            background: {selected_background};
            border: 1px solid {border};
            border-radius: {radius}px;
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


def _chip(text: str, color: str, background: str | None = None) -> QLabel:
    chip = QLabel(text)
    chip.setWordWrap(True)
    chip.setStyleSheet(
        f"background: {background or COLORS['accent_dark']}; border: 1px solid {color}; "
        f"border-radius: 10px; padding: 5px 9px; color: {color}; font-weight: 800;"
    )
    return chip


class ChartWidget(QWidget):
    def __init__(
        self,
        block: dict[str, Any],
        presentation: bool = False,
        palette: dict[str, str] | None = None,
    ) -> None:
        super().__init__()
        self.block = block
        self.presentation = presentation
        self.palette = palette or _visual_palette()
        self.setMinimumHeight(340 if presentation else 230)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())

    def sizeHint(self) -> QSize:  # type: ignore[override]
        return QSize(780, 360 if self.presentation else 240)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(self.palette["card"]))
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
        accent = QColor(self.palette["accent"])
        muted = QColor(COLORS["muted"])
        grid_pen = QPen(QColor(self.palette["border"]))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for step in range(1, 4):
            y = rect.top() + rect.height() * step / 4
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
        painter.setPen(Qt.PenStyle.NoPen)
        for index, value in enumerate(values):
            ratio = max(0.0, min(1.0, value / maximum))
            height = max(6, int(rect.height() * ratio))
            x = rect.left() + index * (bar_width + gap)
            y = rect.bottom() - height
            bar = QRectF(x, y, bar_width, height)
            painter.setBrush(accent if index % 2 == 0 else QColor(self.palette["accent_2"]))
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
            painter.setBrush(QColor(self.palette["card_soft"]))
            painter.drawRoundedRect(bar_rect, 7, 7)
            fill = QRectF(bar_rect.left(), bar_rect.top(), bar_rect.width() * max(0, value / maximum), bar_rect.height())
            painter.setBrush(QColor(self.palette["accent"]))
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
        colors = [
            QColor(self.palette["accent"]),
            QColor(self.palette["accent_2"]),
            QColor(self.palette["accent_3"]),
            QColor(self.palette["success"]),
            QColor(self.palette["warning"]),
        ]
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
            painter.setBrush(QColor(self.palette["card_soft"]))
            painter.drawRoundedRect(bar, 6, 6)
            painter.setBrush(QColor(self.palette["accent"]))
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
    def __init__(self, presentation: bool = False, style: object | None = None) -> None:
        self.presentation = presentation
        self.preset = get_visual_preset(style)
        self.palette = dict(self.preset.palette)
        typography = self.preset.typography
        self.title_size = (
            typography.presentation_title_size if presentation else typography.title_size
        )
        self.section_title_size = (
            typography.presentation_section_title_size
            if presentation
            else typography.section_title_size
        )
        self.body_size = typography.presentation_body_size if presentation else typography.body_size

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

    def render_block(
        self,
        block: dict[str, Any],
        root_title: object | None = None,
        root_subtitle: object | None = None,
    ) -> QWidget:
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
        if block_type in {"mindmap", "concept_map"}:
            return self._concept_map(block, block_type)
        if block_type == "exam_trap":
            return self._exam_trap(block)
        if block_type == "source_quote":
            return self._source_quote(block)
        if block_type == "quiz_preview":
            return self._quiz_preview(block)
        return self._section(block)

    def _panel(self, elevated: bool = False, accent: str | None = None, tone: str = "default") -> QFrame:
        background = self.palette["card_alt"] if elevated else self.palette["card"]
        if tone == "soft":
            background = self.palette["card_soft"]
        return _panel(
            elevated=elevated,
            accent=accent or self.palette["border"],
            background=background,
            radius=self.preset.card_style.radius,
        )

    def _hero(
        self,
        block: dict[str, Any],
        root_title: object | None = None,
        root_subtitle: object | None = None,
    ) -> QWidget:
        panel = QFrame()
        panel.setObjectName("VisualHeroPanel")
        panel.setMinimumHeight(
            self.preset.hero_style.presentation_minimum_height
            if self.presentation
            else self.preset.hero_style.minimum_height
        )
        panel.setStyleSheet(
            f"""
            QFrame#VisualHeroPanel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.palette['card_alt']},
                    stop:0.55 {self.palette['card']},
                    stop:1 {self.palette['card_soft']});
                border: 1px solid {self.palette['accent_2']};
                border-radius: {self.preset.hero_style.radius}px;
            }}
            """
        )
        layout = QVBoxLayout(panel)
        margins = self.preset.spacing.hero_margin + (12 if self.presentation else 0)
        layout.setContentsMargins(margins, margins, margins, margins)
        layout.setSpacing(14)
        eyebrow = str(root_subtitle or block.get("eyebrow") or block.get("subtitle") or "").strip()
        if eyebrow:
            layout.addWidget(_chip(eyebrow, self.palette["accent_3"], self.palette["card_soft"]))
        title = _title(str(block.get("title") or root_title or "Resumo visual"), "HeroTitle", self.title_size)
        title.setStyleSheet(
            f"font-size: {self.title_size}px; font-weight: 900; color: {COLORS['text']};"
        )
        layout.addWidget(title)
        text = str(block.get("text") or block.get("content") or "")
        if text:
            layout.addWidget(_body(text, self.body_size + (1 if self.presentation else 0), COLORS["text"]))
        highlights = block.get("items") if isinstance(block.get("items"), list) else []
        if highlights:
            row = QHBoxLayout()
            row.setSpacing(8)
            for item in highlights[:4]:
                row.addWidget(_chip(str(item), self.palette["accent"]))
            row.addStretch()
            layout.addLayout(row)
        return panel

    def _section(self, block: dict[str, Any]) -> QWidget:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)
        layout.addWidget(_title(str(block.get("title") or "Secao"), "SectionTitle", self.section_title_size))
        text = str(block.get("text") or block.get("content") or "")
        if text:
            layout.addWidget(_body(text, self.body_size))
        return panel

    def _cards(self, block: dict[str, Any]) -> QWidget:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        layout.addWidget(_title(str(block.get("title") or "Cards"), "SectionTitle", self.section_title_size))
        text = str(block.get("text") or "")
        if text:
            layout.addWidget(_body(text, self.body_size))
        items = block.get("items") if isinstance(block.get("items"), list) else []
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        columns = 2 if self.presentation or len(items) < 5 else 3
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            accent = [self.palette["accent"], self.palette["accent_2"], self.palette["accent_3"]][index % 3]
            card = self._panel(elevated=True, accent=accent)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(8)
            header = QHBoxLayout()
            icon = str(item.get("icon") or item.get("emoji") or "").strip()
            if icon:
                icon_label = QLabel(icon[:3])
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                icon_label.setFixedSize(34, 34)
                icon_label.setStyleSheet(
                    f"background: {self.palette['card_soft']}; border: 1px solid {accent}; "
                    f"border-radius: 10px; color: {COLORS['text']}; font-size: 17px;"
                )
                header.addWidget(icon_label)
            header.addWidget(_title(str(item.get("title") or f"Item {index + 1}"), "SmallTitle"))
            header.addStretch()
            card_layout.addLayout(header)
            if item.get("text"):
                card_layout.addWidget(_body(str(item.get("text")), self.body_size))
            self._add_points(card_layout, item)
            grid.addWidget(card, index // columns, index % columns)
        layout.addLayout(grid)
        return panel

    def _callout(self, block: dict[str, Any]) -> QWidget:
        variant = str(block.get("variant") or "info").lower()
        color = {
            "info": self.palette["accent"],
            "success": self.palette["success"],
            "warning": self.palette["warning"],
            "danger": self.palette["danger"],
            "tip": self.palette["accent_3"],
            "exam": self.palette["accent_2"],
            "example": self.palette["success"],
            "formula": self.palette["accent"],
        }.get(variant, self.palette["accent"])
        panel = self._panel(elevated=True, accent=color, tone="soft")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(9)
        header = QHBoxLayout()
        header.addWidget(_chip(variant.upper(), color, self.palette["card"]))
        header.addWidget(_title(str(block.get("title") or "Destaque"), "SectionTitle", self.section_title_size))
        header.addStretch()
        layout.addLayout(header)
        text = str(block.get("text") or "")
        if text:
            layout.addWidget(_body(text, self.body_size, COLORS["text"]))
        self._add_item_list(layout, block)
        return panel

    def _table(self, block: dict[str, Any]) -> QWidget:
        panel = self._panel()
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
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setWordWrap(True)
        table.verticalHeader().hide()
        table.setHorizontalHeaderLabels([str(headers[index]) if index < len(headers) else "" for index in range(column_count)])
        for row_index, row in enumerate(rows):
            values = row if isinstance(row, list) else []
            table.setRowHeight(row_index, 46 if self.presentation else 38)
            for column_index, value in enumerate(values[:column_count]):
                item = QTableWidgetItem(str(value))
                item.setForeground(QColor(COLORS["text"]))
                table.setItem(row_index, column_index, item)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        table.resizeRowsToContents()
        table.setMinimumHeight(min(460 if self.presentation else 340, 94 + max(1, len(rows)) * 48))
        table.setStyleSheet(
            f"""
            QTableWidget {{
                background: {self.palette['card_alt']};
                border: 1px solid {self.palette['border']};
                border-radius: 14px;
                alternate-background-color: {self.palette['card_soft']};
                gridline-color: transparent;
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {self.palette['border']};
            }}
            QHeaderView::section {{
                background: {self.palette['card_soft']};
                color: {self.palette['accent_3']};
                font-weight: 800;
                padding: 11px;
                border: 0;
                border-bottom: 1px solid {self.palette['accent']};
            }}
            """
        )
        layout.addWidget(table)
        return panel

    def _comparison(self, block: dict[str, Any]) -> QWidget:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        layout.addWidget(_title(str(block.get("title") or "Comparacao"), "SectionTitle", self.section_title_size))
        items = block.get("items") if isinstance(block.get("items"), list) else []
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        columns = min(max(len(items), 1), 3)
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            accent = self.palette["success"] if item.get("pros") else self.palette["accent_2"]
            card = self._panel(elevated=True, accent=accent)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(8)
            card_layout.addWidget(_title(str(item.get("title") or f"Item {index + 1}"), "SmallTitle"))
            if item.get("text"):
                card_layout.addWidget(_body(str(item.get("text")), self.body_size))
            self._add_points(card_layout, item)
            self._add_pros_cons(card_layout, item)
            grid.addWidget(card, index // columns, index % columns)
        layout.addLayout(grid)
        return panel

    def _sequence(self, block: dict[str, Any], block_type: str) -> QWidget:
        title_map = {"steps": "Passos", "timeline": "Linha do tempo", "mistakes": "Erros comuns"}
        accent = self.palette["danger"] if block_type == "mistakes" else self.palette["accent"]
        panel = self._panel(accent=accent)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)
        layout.addWidget(_title(str(block.get("title") or title_map[block_type]), "SectionTitle", self.section_title_size))
        if block_type == "mistakes":
            layout.addWidget(_body("Revise estes pontos antes da prova.", self.body_size, COLORS["text"]))
        items = block.get("items") if isinstance(block.get("items"), list) else []
        for index, item in enumerate(items, start=1):
            item_data = item if isinstance(item, dict) else {"title": str(item), "text": "", "number": str(index)}
            row = QHBoxLayout()
            row.setSpacing(12)
            badge_text = "!" if block_type == "mistakes" else str(item_data.get("number") or index)
            badge = QLabel(badge_text)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFixedSize(34, 34)
            badge.setStyleSheet(
                f"background: {self.palette['card_soft']}; border: 1px solid {accent}; "
                f"border-radius: 17px; color: {accent}; font-weight: 900;"
            )
            row.addWidget(badge)
            content_panel = QFrame()
            content_panel.setStyleSheet(
                f"border-left: 2px solid {accent}; padding-left: 10px; background: transparent;"
            )
            content = QVBoxLayout(content_panel)
            content.setContentsMargins(12, 0, 0, 4)
            content.setSpacing(4)
            title = str(item_data.get("title") or "")
            text = str(item_data.get("text") or "")
            if title:
                content.addWidget(_title(title, "SmallTitle"))
            if text:
                content.addWidget(_body(text, self.body_size))
            if not title and not text:
                content.addWidget(_body(str(item), self.body_size))
            row.addWidget(content_panel, 1)
            layout.addLayout(row)
        return panel

    def _tags(self, block: dict[str, Any]) -> QWidget:
        panel = self._panel()
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
            tag = _chip(str(item), self.palette["accent_3"], self.palette["card_alt"])
            tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(tag, index // columns, index % columns)
        layout.addLayout(grid)
        return panel

    def _definition_like(self, block: dict[str, Any], block_type: str) -> QWidget:
        title = str(block.get("title") or {"formula": "Formula", "definition": "Definicao", "example": "Exemplo"}[block_type])
        text = str(block.get("text") or block.get("definition") or block.get("content") or "")
        accent = self.palette["accent"] if block_type != "example" else self.palette["success"]
        panel = self._panel(elevated=True, accent=accent)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)
        layout.addWidget(_title(title, "SectionTitle", self.section_title_size))
        if text:
            if block_type == "formula":
                formula = QLabel(text)
                formula.setWordWrap(True)
                formula.setFont(QFont("Consolas", 18 if self.presentation else 15))
                formula.setStyleSheet(
                    f"background: {self.palette['card_soft']}; border: 1px solid {accent}; "
                    f"border-radius: 14px; padding: 16px; color: {COLORS['text']}; font-weight: 800;"
                )
                layout.addWidget(formula)
            else:
                layout.addWidget(_body(text, self.body_size, COLORS["text"]))
        self._add_item_list(layout, block, strong_body=block_type == "formula")
        return panel

    def _flow(self, block: dict[str, Any]) -> QWidget:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        layout.addWidget(_title(str(block.get("title") or "Fluxo"), "SectionTitle", self.section_title_size))
        items = block.get("items") if isinstance(block.get("items"), list) else []
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(10)
        row = 0
        column = 0
        max_columns = 5 if self.presentation else 7
        for index, item in enumerate(items):
            if column >= max_columns:
                row += 1
                column = 0
            pill = QLabel(str(item))
            pill.setWordWrap(True)
            pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pill.setStyleSheet(
                f"background: {self.palette['card_alt']}; border: 1px solid {self.palette['accent']}; "
                f"border-radius: 14px; padding: 10px 13px; color: {COLORS['text']}; font-weight: 800;"
            )
            grid.addWidget(pill, row, column)
            column += 1
            if index < len(items) - 1:
                if column >= max_columns:
                    row += 1
                    column = 0
                arrow = QLabel("->")
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                arrow.setStyleSheet(f"color: {self.palette['accent_3']}; font-weight: 900; font-size: 18px;")
                grid.addWidget(arrow, row, column)
                column += 1
        layout.addLayout(grid)
        return panel

    def _chart(self, block: dict[str, Any]) -> QWidget:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)
        layout.addWidget(_title(str(block.get("title") or "Grafico"), "SectionTitle", self.section_title_size))
        description = str(block.get("description") or "")
        if description:
            layout.addWidget(_body(description, self.body_size))
        chart = ChartWidget(block, presentation=self.presentation, palette=self.palette)
        chart.setStyleSheet(f"background: {self.palette['card']}; border-radius: 14px;")
        layout.addWidget(chart)
        unit = str(block.get("unit") or "")
        interpretation = str(block.get("interpretation") or block.get("insight") or "")
        footer = "Unidade: " + unit if unit else ""
        if footer:
            layout.addWidget(_body(footer, 12, COLORS["weak"]))
        if interpretation:
            layout.addWidget(_chip(f"Interpretacao: {interpretation}", self.palette["accent_3"], self.palette["card_soft"]))
        return panel

    def _concept_map(self, block: dict[str, Any], block_type: str) -> QWidget:
        panel = self._panel(accent=self.palette["accent_2"])
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        title = "Mapa mental" if block_type == "mindmap" else "Mapa de conceitos"
        layout.addWidget(_title(str(block.get("title") or title), "SectionTitle", self.section_title_size))
        text = str(block.get("text") or "")
        if text:
            layout.addWidget(_body(text, self.body_size))
        items = block.get("items") if isinstance(block.get("items"), list) else []
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        columns = 3 if not self.presentation else 2
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            node = self._panel(elevated=True, accent=[self.palette["accent"], self.palette["accent_2"], self.palette["accent_3"]][index % 3])
            node_layout = QVBoxLayout(node)
            node_layout.setContentsMargins(14, 12, 14, 12)
            node_layout.setSpacing(6)
            node_layout.addWidget(_title(str(item.get("title") or f"No {index + 1}"), "SmallTitle"))
            if item.get("text"):
                node_layout.addWidget(_body(str(item.get("text")), self.body_size))
            self._add_points(node_layout, item)
            grid.addWidget(node, index // columns, index % columns)
        layout.addLayout(grid)
        return panel

    def _exam_trap(self, block: dict[str, Any]) -> QWidget:
        trap = dict(block)
        trap["variant"] = "exam"
        trap.setdefault("title", "Pegadinha de prova")
        return self._callout(trap)

    def _source_quote(self, block: dict[str, Any]) -> QWidget:
        panel = self._panel(elevated=True, accent=self.palette["accent_3"], tone="soft")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)
        layout.addWidget(_title(str(block.get("title") or "Trecho fonte"), "SectionTitle", self.section_title_size))
        quote = str(block.get("quote") or block.get("text") or block.get("content") or "")
        if quote:
            quote_label = QLabel(f'"{quote}"')
            quote_label.setWordWrap(True)
            quote_label.setStyleSheet(
                f"color: {COLORS['text']}; font-size: {self.body_size + 2}px; "
                f"font-weight: 700; line-height: 1.4;"
            )
            layout.addWidget(quote_label)
        source = str(block.get("source") or "")
        if source:
            layout.addWidget(_chip(source, self.palette["accent_3"], self.palette["card"]))
        return panel

    def _quiz_preview(self, block: dict[str, Any]) -> QWidget:
        panel = self._panel(accent=self.palette["accent"])
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)
        layout.addWidget(_title(str(block.get("title") or "Como pode cair"), "SectionTitle", self.section_title_size))
        items = block.get("items") if isinstance(block.get("items"), list) else []
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                layout.addWidget(_body(str(item), self.body_size))
                continue
            card = self._panel(elevated=True, accent=self.palette["accent_3"])
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            badge = _chip(f"Q{index}", self.palette["accent_3"], self.palette["card_soft"])
            card_layout.addWidget(badge)
            text_box = QVBoxLayout()
            text_box.setSpacing(4)
            text_box.addWidget(_title(str(item.get("title") or item.get("question") or f"Questao {index}"), "SmallTitle"))
            text = str(item.get("text") or item.get("answer") or "")
            if text:
                text_box.addWidget(_body(text, self.body_size))
            card_layout.addLayout(text_box, 1)
            layout.addWidget(card)
        return panel

    def _add_item_list(self, layout: QVBoxLayout, block: dict[str, Any], strong_body: bool = False) -> None:
        items = block.get("items") if isinstance(block.get("items"), list) else []
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                layout.addWidget(_body(str(item), self.body_size))
                continue
            card = self._panel(elevated=True)
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
            self._add_pros_cons(card_layout, item)
            layout.addWidget(card)

    def _add_points(self, layout: QVBoxLayout, item: dict[str, Any]) -> None:
        points = item.get("points") if isinstance(item.get("points"), list) else []
        for point in points:
            layout.addWidget(_body(f"- {point}", self.body_size))

    def _add_pros_cons(self, layout: QVBoxLayout, item: dict[str, Any]) -> None:
        pros = item.get("pros") if isinstance(item.get("pros"), list) else []
        cons = item.get("cons") if isinstance(item.get("cons"), list) else []
        for title, values, color in (
            ("Pros", pros, self.palette["success"]),
            ("Contras", cons, self.palette["danger"]),
        ):
            if not values:
                continue
            layout.addWidget(_chip(title, color, self.palette["card_soft"]))
            for value in values:
                layout.addWidget(_body(f"- {value}", self.body_size))


class VisualSummaryWidget(QWidget):
    def __init__(self, summary_visual: str, presentation: bool = False) -> None:
        super().__init__()
        self.summary_visual = summary_visual
        self.presentation = presentation
        data = parse_visual_summary(summary_visual)
        self.preset = get_visual_preset(data.get("style") if data else "auto")
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
        margins = (
            self.preset.spacing.presentation_margin
            if presentation
            else self.preset.spacing.content_margin
        )
        self.layout.setContentsMargins(margins, margins, margins, margins)
        self.layout.setSpacing(
            self.preset.spacing.presentation_gap if presentation else self.preset.spacing.section_gap
        )
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
        SummaryVisualRenderer(
            self.presentation,
            style=data.get("style") or data.get("theme"),
        ).render_summary(self.layout, data)
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
        self.preset = get_visual_preset(self.data.get("style") if self.data else "auto")
        self.slides = visual_summary_slides(self.data)
        self.index = 0
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(
            self.preset.spacing.panel_margin,
            self.preset.spacing.panel_margin,
            self.preset.spacing.panel_margin,
            self.preset.spacing.panel_margin,
        )
        self.root.setSpacing(self.preset.spacing.section_gap)

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
        slide_layout.setContentsMargins(
            self.preset.spacing.presentation_margin,
            self.preset.spacing.hero_margin,
            self.preset.spacing.presentation_margin,
            self.preset.spacing.hero_margin,
        )
        slide_layout.addStretch(1)
        slide_layout.addWidget(
            SummaryVisualRenderer(
                presentation=True,
                style=(self.data or {}).get("style") if isinstance(self.data, dict) else "auto",
            ).render_block(slide),
            4,
        )
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
