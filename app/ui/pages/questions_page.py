from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from app.application.query_services.study_session_query_service import StudySessionQueryService
from app.application.query_services.ui_data_provider import UIBlock, UIDataProvider, UIModule, UISubject
from app.application.use_cases.answer_question import AnswerQuestionUseCase
from app.core.models.question import Question
from app.core.models.study_block import StudyBlock
from app.core.storage.local_storage import LocalStorage
from app.ui.components.cards import EmptyState, ProgressLine, label
from app.ui.feedback import log_action, show_toast
from app.ui.pages.base import panel, scroll_page
from app.ui.theme import COLORS


class QuestionsPage(QWidget):
    def __init__(self, provider: UIDataProvider, storage: LocalStorage) -> None:
        super().__init__()
        self.provider = provider
        self.study_session_query_service = StudySessionQueryService(storage)
        self.answer_question_use_case = AnswerQuestionUseCase(storage)
        self.subjects = provider.subjects()
        self.current_block: StudyBlock | None = None
        self.questions: list[Question] = []
        self.question_queue: list[dict[str, object]] = []
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
        self.question_queue = []
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
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Todas", "all")
        self.filter_combo.addItem("Não respondidas", "unanswered")
        self.filter_combo.addItem("Erradas", "wrong")
        self.filter_combo.addItem("Corretas", "correct")
        self.subject_combo.currentTextChanged.connect(self._refresh_modules)
        self.module_combo.currentTextChanged.connect(self._refresh_blocks)
        self.block_combo.currentTextChanged.connect(self._load_selected_block)
        self.filter_combo.currentTextChanged.connect(self._load_selected_block)
        filters.addWidget(self.subject_combo)
        filters.addWidget(self.module_combo)
        filters.addWidget(self.block_combo, 1)
        filters.addWidget(self.filter_combo)
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
        context = self.study_session_query_service.block_context(block_id)
        subject = next((item for item in self.subjects if item.name == context.subject.name), None)
        if subject:
            subject_index = self.subject_combo.findText(subject.name)
            if subject_index >= 0:
                self.subject_combo.setCurrentIndex(subject_index)
        module_index = self.module_combo.findText(context.module.name)
        if module_index >= 0:
            self.module_combo.setCurrentIndex(module_index)
        block_index = self.block_combo.findData(context.block.id)
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
        session = self.study_session_query_service.question_session(
            str(block_id),
            self._selected_filter_mode(),
        )
        self.current_block = session.block
        self.questions = session.questions
        self.question_queue = session.queue
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
        self.question_queue = self._fresh_question_queue()
        if self.current_index >= len(self.question_queue):
            self.current_index = max(0, len(self.question_queue) - 1)
        if not self.question_queue:
            self.body.addWidget(
                EmptyState(
                    "Nenhuma pergunta neste filtro.",
                    "Troque o filtro ou responda novas perguntas para mudar esta lista.",
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
        session = self.study_session_query_service.question_session(
            self.current_block.id,
            self._selected_filter_mode(),
        )
        progress = session.progress
        queue_item = self.question_queue[self.current_index]
        question = self.questions[int(queue_item["index"])]
        latest_answer = progress.answered_questions.get(question.id, {})
        attempts = progress.question_attempts.get(question.id, [])
        display_answer = self.selected_answer or str(latest_answer.get("selected_answer", "") or "")
        show_result = self.answered or bool(latest_answer)
        qcard = panel()
        qlayout = QVBoxLayout(qcard)
        qlayout.setContentsMargins(24, 22, 24, 22)
        qlayout.setSpacing(14)
        state_label = {
            "unanswered": "não respondida",
            "wrong": "errada",
            "correct": "correta",
        }.get(str(queue_item["state"]), "pergunta")
        qlayout.addWidget(label(f"Questão {self.current_index + 1} de {len(self.question_queue)} • {state_label}", "Weak"))
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
        if show_result:
            qlayout.addWidget(label(f"Gabarito: {question.correct_answer}", "SectionTitle"))
            if latest_answer and not self.selected_answer:
                qlayout.addWidget(label(f"Última resposta: {latest_answer.get('selected_answer', '')}", "Muted"))
            if question.explanation:
                qlayout.addWidget(label(question.explanation, "Muted"))
            self._paint_answers(question, display_answer)
        center.addWidget(qcard)

        controls = QHBoxLayout()
        previous = QPushButton("Anterior")
        previous.clicked.connect(self._previous)
        answer = QPushButton("Responder novamente" if latest_answer and not self.answered else "Responder")
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
        right_layout.addWidget(label("Progresso no bloco", "SectionTitle"))
        percent = int((progress.questions_answered / max(1, progress.questions_total)) * 100)
        wrong_count = len(self.study_session_query_service.question_session(self.current_block.id, "wrong").queue)
        correct_count = len(self.study_session_query_service.question_session(self.current_block.id, "correct").queue)
        unanswered_count = len(self.study_session_query_service.question_session(self.current_block.id, "unanswered").queue)
        right_layout.addWidget(ProgressLine(percent))
        for item in [
            f"Respondidas: {progress.questions_answered}",
            f"Corretas: {correct_count}",
            f"Erradas: {wrong_count}",
            f"Não respondidas: {unanswered_count}",
            f"Tentativas nesta pergunta: {len(attempts)}",
        ]:
            right_layout.addWidget(label(item, "Muted"))
        if attempts:
            right_layout.addWidget(label("Histórico recente", "SectionTitle"))
            for attempt in attempts[-4:]:
                marker = "✓" if attempt.get("is_correct") else "×"
                date = str(attempt.get("answered_at", "")).split("T")[0]
                right_layout.addWidget(label(f"{marker} {attempt.get('selected_answer')} em {date}", "Weak"))
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
                f"border-color: {COLORS['accent']}; background: {COLORS['accent_dark']};"
                if letter == answer
                else ""
            )

    def _answer(self) -> None:
        if not self.current_block or not self.questions or not self.selected_answer:
            show_toast(self, "Selecione uma alternativa antes de responder.", "warning")
            return
        if self.answered:
            show_toast(self, "Esta pergunta já foi respondida nesta tela.", "info")
            return
        queue_item = self.question_queue[self.current_index]
        question = self.questions[int(queue_item["index"])]
        self.answer_question_use_case.execute(
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
        updated_queue = self._fresh_question_queue()
        next_index = next(
            (index for index, item in enumerate(updated_queue) if item["question_id"] == question.id),
            None,
        )
        if next_index is None:
            self.question_queue = updated_queue
            self.current_index = min(self.current_index, max(0, len(updated_queue) - 1))
            self.selected_answer = None
            self.answered = False
        else:
            self.question_queue = updated_queue
            self.current_index = next_index
            self.answered = True
        self._render_session()

    def _paint_answers(self, question: Question, selected_answer: str | None = None) -> None:
        for letter, button in self.option_buttons.items():
            if letter == question.correct_answer:
                button.setStyleSheet(f"border-color: {COLORS['green']}; color: {COLORS['green']};")
            elif letter == (selected_answer or self.selected_answer):
                button.setStyleSheet(f"border-color: {COLORS['red']}; color: {COLORS['red']};")

    def _previous(self) -> None:
        if self.question_queue:
            self.current_index = max(0, self.current_index - 1)
            self.selected_answer = None
            self.answered = False
            self._render_session()

    def _next(self) -> None:
        if self.question_queue:
            self.current_index = min(len(self.question_queue) - 1, self.current_index + 1)
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

    def _fresh_question_queue(self) -> list[dict[str, object]]:
        if not self.current_block:
            return []
        return self.study_session_query_service.question_session(
            self.current_block.id,
            self._selected_filter_mode(),
        ).queue

    def _selected_filter_mode(self) -> str:
        return str(self.filter_combo.currentData() or "all") if hasattr(self, "filter_combo") else "all"

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

