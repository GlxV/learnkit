from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.application.query_services.ui_data_provider import UIBlock, UIModule, UISubject
from app.ui.components.icons import LineIcon
from app.ui.theme import COLORS
from app.ui.components.visual import IconBadge, add_shadow


def label(text: str, object_name: str | None = None) -> QLabel:
    item = QLabel(text)
    if object_name:
        item.setObjectName(object_name)
    item.setWordWrap(True)
    return item


class ProgressLine(QProgressBar):
    def __init__(self, value: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setRange(0, 100)
        self.setValue(value)
        self.setTextVisible(False)
        self.setFixedHeight(8)


class StatCard(QFrame):
    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str = "",
        icon: str = "•",
        color: str | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("StatCard")
        self.setMinimumHeight(104)
        self.setMaximumHeight(116)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        add_shadow(self, blur=22, y_offset=8, alpha=52)
        selected_color = color or COLORS["accent"]
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        icon_shell = QFrame()
        icon_shell.setFixedSize(52, 52)
        icon_shell.setStyleSheet(
            f"background: {COLORS['accent_dark']}; "
            f"border: 1px solid {COLORS['border_hover']}; "
            "border-radius: 26px;"
        )
        shell_layout = QHBoxLayout(icon_shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shell_layout.addWidget(LineIcon(icon, selected_color, 25))
        layout.addWidget(icon_shell)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        value_label = label(value)
        value_label.setStyleSheet("font-size: 26px; font-weight: 800;")
        title_label = label(title, "Muted")
        text_box.addWidget(value_label)
        text_box.addWidget(title_label)
        if subtitle:
            subtitle_label = label(subtitle, "Weak")
            subtitle_label.setStyleSheet(f"color: {selected_color}; font-size: 12px;")
            text_box.addWidget(subtitle_label)
        layout.addLayout(text_box, 1)


class SubjectCard(QFrame):
    clicked = Signal(str)

    def __init__(self, subject: UISubject) -> None:
        super().__init__()
        self.subject = subject
        self.setObjectName("SubjectCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        add_shadow(self, blur=18, y_offset=6, alpha=45)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        layout.addWidget(IconBadge(subject.icon, subject.color, size=42, radius=11, font_size=16))

        middle = QVBoxLayout()
        middle.setSpacing(6)
        middle.addWidget(label(subject.name, "SmallTitle"))
        middle.addWidget(ProgressLine(subject.progress))
        layout.addLayout(middle, 1)

        percent = label(f"{subject.progress}%")
        percent.setStyleSheet(f"color: {COLORS['muted']}; font-weight: 700;")
        layout.addWidget(percent)
        layout.addWidget(label(">", "Muted"))

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self.clicked.emit(self.subject.name)
        super().mousePressEvent(event)


class ModuleCard(QFrame):
    clicked = Signal(str)

    def __init__(self, module: UIModule) -> None:
        super().__init__()
        self.module = module
        self.setObjectName("ModuleCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        header = QHBoxLayout()
        header.addWidget(label(module.name, "SmallTitle"))
        header.addStretch()
        header.addWidget(label(f"{len(module.blocks)} blocos", "Muted"))
        layout.addLayout(header)
        layout.addWidget(ProgressLine(module.progress))
        actions = QHBoxLayout()
        actions.addWidget(label(f"{module.progress}% concluído", "Weak"))
        actions.addStretch()
        actions.addWidget(label("...", "Muted"))
        layout.addLayout(actions)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self.clicked.emit(self.module.name)
        super().mousePressEvent(event)


class StudyBlockRow(QFrame):
    open_requested = Signal(str)
    selection_changed = Signal(str, bool)

    def __init__(
        self,
        block: UIBlock,
        *,
        selectable: bool = False,
        selected: bool = False,
    ) -> None:
        super().__init__()
        self.block = block
        self.setObjectName("SelectedStudyBlockRow" if selected else "StudyBlockRow")
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if block.id else Qt.CursorShape.ArrowCursor
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)
        name_box = QVBoxLayout()
        name_box.addWidget(label(block.title, "SmallTitle"))
        name_box.addWidget(label(block.summary, "Weak"))
        layout.addLayout(name_box, 2)
        layout.addWidget(ProgressLine(block.progress), 1)
        layout.addWidget(label(str(block.flashcards), "Muted"))
        layout.addWidget(label(str(block.questions), "Muted"))
        if selectable and block.id:
            selection = QPushButton("Selecionado" if selected else "Selecionar")
            selection.setObjectName("SelectionChip")
            selection.setCheckable(True)
            selection.setChecked(selected)
            selection.clicked.connect(
                lambda checked=False: self.selection_changed.emit(block.id or "", checked)
            )
            layout.addWidget(selection)
        action = QPushButton("Estudar")
        action.setObjectName("GhostButton")
        if block.id:
            action.clicked.connect(lambda: self.open_requested.emit(block.id or ""))
        else:
            action.setEnabled(False)
            action.setToolTip("Disponivel quando o bloco estiver salvo no storage real.")
        layout.addWidget(action)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if self.block.id:
            self.open_requested.emit(self.block.id)
        super().mousePressEvent(event)


class EmptyState(QFrame):
    def __init__(self, title: str, subtitle: str) -> None:
        super().__init__()
        self.setObjectName("Panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(8)
        layout.addWidget(label(title, "SectionTitle"))
        layout.addWidget(label(subtitle, "Muted"))


class FlashcardViewer(QFrame):
    def __init__(self, question: str, answer: str) -> None:
        super().__init__()
        self.setObjectName("Panel")
        self.question = question
        self.answer = answer
        self.showing_answer = False
        self.setMinimumHeight(320)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(16)
        self.badge = label("Frente", "Weak")
        self.content = label(question)
        self.content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content.setStyleSheet("font-size: 25px; font-weight: 700;")
        hint = label("Clique para virar o card", "Muted")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.badge)
        layout.addStretch()
        layout.addWidget(self.content)
        layout.addWidget(hint)
        layout.addStretch()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_side_style()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self.showing_answer = not self.showing_answer
        self.badge.setText("Verso" if self.showing_answer else "Frente")
        self.content.setText(self.answer if self.showing_answer else self.question)
        self._apply_side_style()
        super().mousePressEvent(event)

    def _apply_side_style(self) -> None:
        if self.showing_answer:
            self.setStyleSheet(
                f"""
                QFrame#Panel {{
                    background: {COLORS['card_alt']};
                    border: 1px solid {COLORS['accent']};
                    border-radius: 16px;
                }}
                """
            )
            self.badge.setStyleSheet(f"color: {COLORS['success']}; font-weight: 800;")
        else:
            self.setStyleSheet(
                f"""
                QFrame#Panel {{
                    background: {COLORS['card']};
                    border: 1px solid {COLORS['border_hover']};
                    border-radius: 16px;
                }}
                """
            )
            self.badge.setStyleSheet(f"color: {COLORS['accent_hover']}; font-weight: 800;")


class QuestionViewer(QFrame):
    option_selected = Signal(str)

    def __init__(self, statement: str, alternatives: dict[str, str]) -> None:
        super().__init__()
        self.setObjectName("Panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        layout.addWidget(label("Questão 7 de 20  •  Múltipla escolha", "Weak"))
        statement_label = label(statement)
        statement_label.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(statement_label)
        for key, value in alternatives.items():
            option = QPushButton(f"{key}) {value}")
            option.setObjectName("GhostButton")
            option.clicked.connect(lambda checked=False, selected=key: self.option_selected.emit(selected))
            option.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            layout.addWidget(option)
