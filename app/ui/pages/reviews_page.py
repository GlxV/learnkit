from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.application.dto.review_cycle import ReviewQueueDTO, ReviewQueueItemDTO
from app.application.query_services.review_cycle_query_service import ReviewCycleQueryService
from app.application.query_services.ui_data_provider import UIDataProvider
from app.application.use_cases.answer_question import AnswerQuestionUseCase
from app.application.use_cases.manage_review_cycle import ManageReviewCycleUseCase
from app.application.use_cases.review_flashcard import ReviewFlashcardUseCase
from app.core.models.flashcard import Flashcard
from app.core.models.question import Question
from app.core.storage.local_storage import LocalStorage
from app.ui.components.cards import EmptyState, FlashcardViewer, StatCard, label
from app.ui.feedback import log_action, show_toast
from app.ui.pages.base import panel, scroll_page
from app.ui.theme import COLORS


STEP_LABELS = {
    "1h": "Revisão de 1h",
    "24h": "Revisão de 24h",
    "7d": "Revisão semanal",
    "30d": "Revisão mensal",
}


class ReviewSessionDialog(QDialog):
    status_changed = Signal()

    def __init__(
        self,
        storage: LocalStorage,
        schedule_id: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.storage = storage
        self.query_service = ReviewCycleQueryService(storage)
        self.review_cycle_use_case = ManageReviewCycleUseCase(storage)
        self.review_flashcard_use_case = ReviewFlashcardUseCase(storage)
        self.answer_question_use_case = AnswerQuestionUseCase(storage)
        self.session = self.query_service.session(schedule_id)
        self.selected_answers: dict[str, str] = {}
        self.setObjectName("ReviewSessionDialog")
        self.setWindowTitle(f"{STEP_LABELS.get(self.session.review.review_step, 'Revisão')} - {self.session.review.block_title}")
        self.resize(880, 760)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        layout.addWidget(label(self.session.review.block_title, "Title"))
        layout.addWidget(
            label(
                f"{self.session.review.subject_name} > {self.session.review.module_name}  •  "
                f"{STEP_LABELS.get(self.session.review.review_step, self.session.review.review_step)}  •  "
                f"{_local_datetime(self.session.review.scheduled_at)}",
                "Muted",
            )
        )

        scroll, _content, content_layout = scroll_page()
        scroll.setObjectName("ReviewSessionScroll")
        scroll.viewport().setObjectName("ReviewSessionViewport")
        _content.setObjectName("ReviewSessionContent")
        content_layout.setContentsMargins(0, 0, 0, 0)
        for section in self._section_order():
            if section == "summary" and self.session.summary_text.strip():
                content_layout.addWidget(self._summary_panel())
            elif section == "flashcards" and self.session.flashcards:
                content_layout.addWidget(self._flashcards_panel())
            elif section == "questions" and self.session.questions:
                content_layout.addWidget(self._questions_panel())
        if not self.session.summary_text.strip() and not self.session.flashcards and not self.session.questions:
            content_layout.addWidget(
                EmptyState(
                    "Este bloco não possui itens ativos para revisar.",
                    "Você ainda pode concluir ou pular esta revisão.",
                )
            )
        content_layout.addStretch()
        layout.addWidget(scroll, 1)

        footer = QWidget()
        footer.setObjectName("ReviewSessionFooter")
        actions = QHBoxLayout(footer)
        actions.setContentsMargins(0, 0, 0, 0)
        skip = QPushButton("Pular")
        skip.clicked.connect(lambda: self._finish("skipped"))
        close = QPushButton("Fechar")
        close.clicked.connect(self.reject)
        complete = QPushButton("Concluir revisão")
        complete.setObjectName("PrimaryButton")
        complete.clicked.connect(lambda: self._finish("done"))
        actions.addWidget(skip)
        actions.addStretch()
        actions.addWidget(close)
        actions.addWidget(complete)
        layout.addWidget(footer)

    def _section_order(self) -> tuple[str, ...]:
        if self.session.review.review_step == "24h":
            return ("questions", "flashcards", "summary")
        if self.session.review.review_step in {"7d", "30d"}:
            return ("summary", "questions", "flashcards")
        return ("summary", "flashcards", "questions")

    def _summary_panel(self) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        layout.addWidget(label("Mini resumo", "SectionTitle"))
        viewer = QTextBrowser()
        viewer.setMarkdown(self.session.summary_text[:1200])
        viewer.setMaximumHeight(180)
        layout.addWidget(viewer)
        return card

    def _flashcards_panel(self) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(label("Flashcards", "SectionTitle"))
        for flashcard in self.session.flashcards:
            layout.addWidget(FlashcardViewer(flashcard.question, flashcard.answer))
            actions = QHBoxLayout()
            for text, status in (
                ("Repetir", "again"),
                ("Difícil", "hard"),
                ("Bom", "good"),
                ("Dominei", "easy"),
            ):
                action = QPushButton(text)
                action.clicked.connect(
                    lambda checked=False, item=flashcard, value=status: self._rate_card(item, value)
                )
                actions.addWidget(action)
            layout.addLayout(actions)
        return card

    def _questions_panel(self) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(label("Perguntas rápidas", "SectionTitle"))
        for question in self.session.questions:
            layout.addWidget(label(question.statement, "SmallTitle"))
            buttons: dict[str, QPushButton] = {}
            for letter in ("A", "B", "C", "D"):
                button = QPushButton(f"{letter}) {question.alternatives.get(letter, '')}")
                button.setObjectName("GhostButton")
                button.clicked.connect(
                    lambda checked=False, q=question, selected=letter, group=buttons: (
                        self._select_answer(q, selected, group)
                    )
                )
                buttons[letter] = button
                layout.addWidget(button)
            feedback = label("", "Muted")
            answer = QPushButton("Responder")
            answer.setObjectName("PrimaryButton")
            answer.clicked.connect(
                lambda checked=False, q=question, message=feedback, group=buttons, action=answer: (
                    self._submit_answer(q, message, group, action)
                )
            )
            layout.addWidget(answer)
            layout.addWidget(feedback)
        return card

    def _rate_card(self, flashcard: Flashcard, status: str) -> None:
        self.review_flashcard_use_case.execute(self.session.review.block_id, flashcard.id, status)
        show_toast(self, "Flashcard registrado nesta revisão.", "success")

    def _select_answer(
        self,
        question: Question,
        selected: str,
        buttons: dict[str, QPushButton],
    ) -> None:
        self.selected_answers[question.id] = selected
        for letter, button in buttons.items():
            button.setStyleSheet(
                f"border-color: {COLORS['accent']}; background: {COLORS['accent_dark']};"
                if letter == selected
                else ""
            )

    def _submit_answer(
        self,
        question: Question,
        feedback: QLabel,
        buttons: dict[str, QPushButton],
        action: QPushButton,
    ) -> None:
        selected = self.selected_answers.get(question.id)
        if not selected:
            show_toast(self, "Selecione uma alternativa antes de responder.", "warning")
            return
        self.answer_question_use_case.execute(
            self.session.review.block_id,
            question.id,
            selected,
            question.correct_answer,
        )
        correct = selected == question.correct_answer
        feedback.setText(
            "Resposta correta."
            if correct
            else f"Resposta incorreta. Gabarito: {question.correct_answer}."
        )
        feedback.setStyleSheet(f"color: {COLORS['green' if correct else 'red']};")
        for button in buttons.values():
            button.setEnabled(False)
        action.setEnabled(False)

    def _finish(self, status: str) -> None:
        if status == "done":
            self.review_cycle_use_case.complete_review(self.session.review.schedule_id)
        else:
            self.review_cycle_use_case.skip_review(self.session.review.schedule_id)
        log_action(
            "block_review_finished",
            schedule_id=self.session.review.schedule_id,
            status=status,
        )
        self.status_changed.emit()
        self.accept()


class ReviewsPage(QWidget):
    def __init__(self, provider: UIDataProvider, storage: LocalStorage) -> None:
        super().__init__()
        self.provider = provider
        self.storage = storage
        self.query_service = ReviewCycleQueryService(storage)
        self.review_cycle_use_case = ManageReviewCycleUseCase(storage)
        self.subject_filter = "Todas as matérias"
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll, _content, self.layout = scroll_page()
        root.addWidget(scroll)
        self.refresh()

    def set_subject_filter(self, subject_name: str) -> None:
        self.subject_filter = subject_name or "Todas as matérias"

    def refresh(self) -> None:
        self._clear_layout(self.layout)
        subject_name = None if self.subject_filter == "Todas as matérias" else self.subject_filter
        queue = self.query_service.queue(subject_name=subject_name)
        self.layout.addWidget(label("Fila de Revisões", "Title"))
        self.layout.addWidget(
            label(
                "Ciclos por bloco, separados da prática adaptativa dos flashcards.",
                "Muted",
            )
        )
        stats = QHBoxLayout()
        stats.addWidget(StatCard("Atrasadas", str(queue.overdue_count), "a resolver", "clock", COLORS["red"]))
        stats.addWidget(StatCard("Hoje", str(queue.today_count), "agendadas", "calendar", COLORS["amber"]))
        stats.addWidget(StatCard("Pendentes", str(queue.pending_count), "no ciclo", "progress", COLORS["accent"]))
        self.layout.addLayout(stats)
        if queue.pending_count == 0:
            self.layout.addWidget(
                EmptyState(
                    "Nenhuma revisão pendente.",
                    "Ative um ciclo em um bloco ou habilite a criação automática nas configurações.",
                )
            )
            self.layout.addStretch()
            return
        self.layout.addWidget(self._group("Atrasadas", queue.overdue, "overdue"))
        self.layout.addWidget(self._group("Para agora / hoje", queue.today, "today"))
        self.layout.addWidget(self._group("Próximas", queue.upcoming, "upcoming"))
        self.layout.addStretch()

    def _group(self, title: str, items: list[ReviewQueueItemDTO], state: str) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(label(title, "SectionTitle"))
        if not items:
            layout.addWidget(label("Nenhuma revisão neste grupo.", "Muted"))
            return card
        for item in items:
            layout.addWidget(self._row(item, state))
        return card

    def _row(self, item: ReviewQueueItemDTO, state: str) -> QWidget:
        row = panel()
        is_due_today = state == "today" and _is_due(item.scheduled_at)
        accent = {
            "overdue": COLORS["red"],
            "today": COLORS["amber"],
            "upcoming": COLORS["border_hover"],
        }[state]
        if is_due_today:
            accent = COLORS["red"]
        row.setObjectName("ReviewQueueRow")
        row.setStyleSheet(
            f"QFrame#ReviewQueueRow {{ background: {COLORS['card_alt']}; "
            f"border: 1px solid {accent}; border-radius: 14px; }}"
        )
        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 12, 14, 12)
        text = QVBoxLayout()
        text.addWidget(label(item.block_title, "SmallTitle"))
        text.addWidget(label(f"{item.subject_name} > {item.module_name}", "Weak"))
        layout.addLayout(text, 1)
        meta = QVBoxLayout()
        meta.addWidget(label(STEP_LABELS.get(item.review_step, item.review_step), "SmallTitle"))
        meta.addWidget(label(_local_datetime(item.scheduled_at), "Weak"))
        if is_due_today:
            due_label = label("Para agora", "Weak")
            due_label.setStyleSheet(f"color: {COLORS['red']}; font-weight: 700;")
            meta.addWidget(due_label)
        layout.addLayout(meta)
        review = QPushButton("Revisar")
        review.setObjectName("PrimaryButton")
        review.clicked.connect(lambda checked=False, value=item.schedule_id: self._open_session(value))
        done = QPushButton("Marcar como feita")
        done.clicked.connect(lambda checked=False, value=item.schedule_id: self._mark_done(value))
        skip = QPushButton("Pular")
        skip.clicked.connect(lambda checked=False, value=item.schedule_id: self._skip(value))
        layout.addWidget(review)
        layout.addWidget(done)
        layout.addWidget(skip)
        return row

    def _open_session(self, schedule_id: str) -> None:
        dialog = ReviewSessionDialog(self.storage, schedule_id, self)
        dialog.status_changed.connect(self.refresh)
        dialog.exec()
        self.refresh()

    def _mark_done(self, schedule_id: str) -> None:
        self.review_cycle_use_case.complete_review(schedule_id)
        log_action("block_review_marked_done", schedule_id=schedule_id)
        self.refresh()

    def _skip(self, schedule_id: str) -> None:
        self.review_cycle_use_case.skip_review(schedule_id)
        log_action("block_review_skipped", schedule_id=schedule_id)
        self.refresh()

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())


def _local_datetime(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value).astimezone()
    except ValueError:
        return value
    return parsed.strftime("%d/%m/%Y às %H:%M")


def _is_due(value: str) -> bool:
    try:
        return datetime.fromisoformat(value).astimezone() <= datetime.now().astimezone()
    except ValueError:
        return False
