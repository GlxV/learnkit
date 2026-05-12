from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from app.core.models.question import Question
from app.core.models.study_block import StudyBlock
from app.core.services.progress_service import ProgressService
from app.core.storage.local_storage import LocalStorage
from app.ui.components.cards import EmptyState, ProgressLine, label
from app.ui.feedback import log_action, show_toast
from app.ui.mock_data import UIDataProvider, UIBlock, UIModule, UISubject
from app.ui.pages.base import panel, scroll_page
from app.ui.theme import COLORS


class QuestionsPage(QWidget):
    def __init__(self, provider: UIDataProvider, storage: LocalStorage) -> None:
        super().__init__()
        self.provider = provider
        self.storage = storage
        self.progress_service = ProgressService(storage)
        self.subjects = provider.subjects()
        self.current_block: StudyBlock | None = None
        self.questions: list[Question] = []
        self.current_index = 0
        self.selected_answer: str | None = None
        self.answered = False
        self.option_buttons: dict[str, QPushButton] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll, _, self.layout = scroll_page()
        root.addWidget(scroll)
        self._build()

    def refresh(self) -> None:
        self._clear_layout(self.layout)
        self.subjects = self.provider.subjects()
        self.current_block = None
        self.questions = []
        self.current_index = 0
        self.selected_answer = None
        self.answered = False
        self.option_buttons = {}
        self._build()

    def _build(self) -> None:
        self.layout.addWidget(label("Perguntas", "Title"))
        if not [block for block in self.provider.all_blocks() if block.questions]:
            self.layout.addWidget(
                EmptyState(
                    "Nenhuma pergunta disponível.",
                    "Importe uma resposta da IA para criar perguntas de múltipla escolha.",
                )
            )
            return

        filters = QHBoxLayout()
        self.subject_combo = QComboBox()
        self.subject_combo.addItems([subject.name for subject in self.subjects])
        self.module_combo = QComboBox()
        self.block_combo = QComboBox()
        self.subject_combo.currentTextChanged.connect(self._refresh_modules)
        self.module_combo.currentTextChanged.connect(self._refresh_blocks)
        self.block_combo.currentTextChanged.connect(self._load_selected_block)
        filters.addWidget(self.subject_combo)
        filters.addWidget(self.module_combo)
        filters.addWidget(self.block_combo, 1)
        filters.addStretch()
        self.layout.addLayout(filters)

        self.body = QHBoxLayout()
        self.layout.addLayout(self.body)
        first = next((block for block in self.provider.all_blocks() if block.questions), None)
        if first:
            subject_index = self.subject_combo.findText(first.subject_name)
            if subject_index >= 0:
                self.subject_combo.setCurrentIndex(subject_index)
        self._refresh_modules()
        if first:
            module_index = self.module_combo.findText(first.module_name)
            if module_index >= 0:
                self.module_combo.setCurrentIndex(module_index)
            block_index = self.block_combo.findData(first.id)
            if block_index >= 0:
                self.block_combo.setCurrentIndex(block_index)

    def select_block_by_id(self, block_id: str) -> None:
        self.refresh()
        _, module, block = self.storage.get_block_by_id(block_id)
        subject = next((item for item in self.subjects if any(mod.id == module.id for mod in item.modules)), None)
        if subject:
            subject_index = self.subject_combo.findText(subject.name)
            if subject_index >= 0:
                self.subject_combo.setCurrentIndex(subject_index)
        module_index = self.module_combo.findText(module.name)
        if module_index >= 0:
            self.module_combo.setCurrentIndex(module_index)
        block_index = self.block_combo.findData(block.id)
        if block_index >= 0:
            self.block_combo.setCurrentIndex(block_index)

    def _refresh_modules(self) -> None:
        subject = self._selected_subject()
        self.module_combo.clear()
        if subject:
            self.module_combo.addItems([module.name for module in subject.modules])
        self._refresh_blocks()

    def _refresh_blocks(self) -> None:
        module = self._selected_module()
        self.block_combo.clear()
        if module:
            for block in module.blocks:
                if block.questions > 0:
                    self.block_combo.addItem(block.title, block.id)
        self._load_selected_block()

    def _load_selected_block(self) -> None:
        block_id = self.block_combo.currentData()
        if not block_id:
            return
        _, _, block = self.storage.get_block_by_id(block_id)
        self.current_block = block
        self.questions = block.questions
        self.current_index = 0
        self.selected_answer = None
        self.answered = False
        self._render_session()

    def _render_session(self) -> None:
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        if not self.current_block or not self.questions:
            self.body.addWidget(
                EmptyState(
                    "Este bloco ainda não possui perguntas.",
                    "Importe uma resposta da IA para criar questões.",
                )
            )
            return

        left = panel()
        left.setFixedWidth(290)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.addWidget(label("Conjuntos de questões", "SectionTitle"))
        for block in self.provider.all_blocks():
            if block.questions:
                button = QPushButton(f"{block.title}\n{block.questions} perguntas")
                button.setObjectName("GhostButton")
                button.clicked.connect(lambda checked=False, item=block: self._select_block(item))
                left_layout.addWidget(button)
        left_layout.addStretch()

        center = QVBoxLayout()
        question = self.questions[self.current_index]
        qcard = panel()
        qlayout = QVBoxLayout(qcard)
        qlayout.setContentsMargins(24, 22, 24, 22)
        qlayout.setSpacing(14)
        qlayout.addWidget(label(f"Questão {self.current_index + 1} de {len(self.questions)}", "Weak"))
        statement = label(question.statement, "HeroTitle")
        qlayout.addWidget(statement)
        self.option_buttons = {}
        for letter in ("A", "B", "C", "D"):
            option = question.alternatives.get(letter, "")
            button = QPushButton(f"{letter}) {option}")
            button.setObjectName("GhostButton")
            button.clicked.connect(lambda checked=False, value=letter: self._select_answer(value))
            self.option_buttons[letter] = button
            qlayout.addWidget(button)
        if self.answered:
            qlayout.addWidget(label(f"Gabarito: {question.correct_answer}", "SectionTitle"))
            if question.explanation:
                qlayout.addWidget(label(question.explanation, "Muted"))
            self._paint_answers(question)
        center.addWidget(qcard)

        controls = QHBoxLayout()
        previous = QPushButton("Anterior")
        previous.clicked.connect(self._previous)
        answer = QPushButton("Responder")
        answer.setObjectName("PrimaryButton")
        answer.clicked.connect(self._answer)
        answer.setEnabled(not self.answered)
        next_button = QPushButton("Próxima questão")
        next_button.clicked.connect(self._next)
        controls.addWidget(previous)
        controls.addWidget(answer)
        controls.addWidget(next_button)
        center.addLayout(controls)

        right = panel()
        right.setFixedWidth(300)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 16, 16, 16)
        progress = self.progress_service.get_block_progress(self.current_block.id)
        right_layout.addWidget(label("Progresso no bloco", "SectionTitle"))
        percent = int((progress.questions_answered / max(1, progress.questions_total)) * 100)
        right_layout.addWidget(ProgressLine(percent))
        for item in [
            f"Respondidas: {progress.questions_answered}",
            f"Acertos: {progress.questions_correct}",
            f"Erros: {progress.questions_wrong}",
            f"Em branco: {max(0, progress.questions_total - progress.questions_answered)}",
        ]:
            right_layout.addWidget(label(item, "Muted"))
        right_layout.addStretch()

        self.body.addWidget(left)
        self.body.addLayout(center, 1)
        self.body.addWidget(right)

    def _select_answer(self, answer: str) -> None:
        if self.answered:
            return
        self.selected_answer = answer
        for letter, button in self.option_buttons.items():
            button.setStyleSheet(
                f"border-color: {COLORS['purple_soft']}; background: #182642;"
                if letter == answer
                else ""
            )

    def _answer(self) -> None:
        if not self.current_block or not self.questions or not self.selected_answer:
            show_toast(self, "Selecione uma alternativa antes de responder.", "warning")
            return
        if self.answered:
            show_toast(self, "Esta pergunta ja foi respondida nesta tela.", "info")
            return
        question = self.questions[self.current_index]
        self.progress_service.record_question(
            self.current_block.id,
            question.id,
            self.selected_answer,
            question.correct_answer,
        )
        is_correct = self.selected_answer == question.correct_answer
        show_toast(self, "Resposta correta." if is_correct else "Resposta incorreta.", "success" if is_correct else "warning")
        log_action(
            "question_answered",
            block_id=self.current_block.id,
            question_id=question.id,
            selected=self.selected_answer,
            correct=question.correct_answer,
            is_correct=is_correct,
        )
        self.answered = True
        self._render_session()

    def _paint_answers(self, question: Question) -> None:
        for letter, button in self.option_buttons.items():
            if letter == question.correct_answer:
                button.setStyleSheet(f"border-color: {COLORS['green']}; color: {COLORS['green']};")
            elif letter == self.selected_answer:
                button.setStyleSheet(f"border-color: {COLORS['red']}; color: {COLORS['red']};")

    def _previous(self) -> None:
        if self.questions:
            self.current_index = max(0, self.current_index - 1)
            self.selected_answer = None
            self.answered = False
            self._render_session()

    def _next(self) -> None:
        if self.questions:
            self.current_index = min(len(self.questions) - 1, self.current_index + 1)
            self.selected_answer = None
            self.answered = False
            self._render_session()

    def _select_block(self, block: UIBlock) -> None:
        if block.id:
            index = self.block_combo.findData(block.id)
            if index >= 0:
                self.block_combo.setCurrentIndex(index)

    def _selected_subject(self) -> UISubject | None:
        return next((subject for subject in self.subjects if subject.name == self.subject_combo.currentText()), None)

    def _selected_module(self) -> UIModule | None:
        subject = self._selected_subject()
        if not subject:
            return None
        return next((module for module in subject.modules if module.name == self.module_combo.currentText()), None)

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
