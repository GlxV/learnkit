from __future__ import annotations

from collections.abc import Callable, Mapping

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.application.dto.combined_review import (
    CombinedFlashcardDTO,
    CombinedQuestionDTO,
    CombinedReviewOriginDTO,
)
from app.application.query_services.study_session_query_service import StudySessionQueryService
from app.application.use_cases.answer_question import AnswerQuestionUseCase
from app.application.use_cases.review_flashcard import ReviewFlashcardUseCase
from app.core.storage.local_storage import LocalStorage
from app.ui.components.cards import EmptyState, FlashcardViewer, label
from app.ui.feedback import log_action, show_toast
from app.ui.pages.base import panel, scroll_page
from app.ui.theme import COLORS


class CombinedReviewSessionDialog(QDialog):
    def __init__(
        self,
        storage: LocalStorage,
        block_ids: list[str],
        settings_provider: Callable[[], Mapping[str, object]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.study_session_query_service = StudySessionQueryService(storage, settings_provider)
        self.review_flashcard_use_case = ReviewFlashcardUseCase(storage)
        self.answer_question_use_case = AnswerQuestionUseCase(storage)
        self.session = self.study_session_query_service.combined_review_session(block_ids)
        self.selected_answers: dict[str, str] = {}
        self.setObjectName("CombinedReviewSessionDialog")
        self.setWindowTitle(f"Revisão combinada - {len(self.session.blocks)} blocos")
        self.resize(980, 780)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        layout.addWidget(label("Revisão combinada", "Title"))
        layout.addWidget(
            label(
                "Sessão temporária: seus blocos permanecem separados "
                "e o progresso volta para cada origem.",
                "Muted",
            )
        )
        layout.addWidget(self._included_blocks_panel())

        scroll, content, content_layout = scroll_page()
        scroll.setObjectName("CombinedReviewSessionScroll")
        scroll.viewport().setObjectName("CombinedReviewSessionViewport")
        content.setObjectName("CombinedReviewSessionContent")
        content_layout.setContentsMargins(0, 0, 0, 0)
        if self.session.summaries:
            content_layout.addWidget(self._summary_panel())
        if self.session.flashcards:
            content_layout.addWidget(self._flashcards_panel())
        if self.session.questions:
            content_layout.addWidget(self._questions_panel())
        if (
            not self.session.summaries
            and not self.session.flashcards
            and not self.session.questions
        ):
            content_layout.addWidget(
                EmptyState(
                    "Nenhum conteúdo disponível para esta seleção.",
                    "Feche a sessão ou selecione blocos com materiais de estudo.",
                )
            )
        content_layout.addStretch()
        layout.addWidget(scroll, 1)

        footer = QWidget()
        footer.setObjectName("CombinedReviewSessionFooter")
        actions = QHBoxLayout(footer)
        actions.setContentsMargins(0, 0, 0, 0)
        skip = QPushButton("Pular")
        skip.clicked.connect(self._skip)
        close = QPushButton("Fechar")
        close.clicked.connect(self.reject)
        complete = QPushButton("Concluir revisão")
        complete.setObjectName("PrimaryButton")
        complete.clicked.connect(self._complete)
        actions.addWidget(skip)
        actions.addStretch()
        actions.addWidget(close)
        actions.addWidget(complete)
        layout.addWidget(footer)

    def _included_blocks_panel(self) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)
        layout.addWidget(label(f"Blocos incluídos ({len(self.session.blocks)})", "SectionTitle"))
        layout.addWidget(
            label("  |  ".join(block.block_title for block in self.session.blocks), "Muted")
        )
        return card

    def _summary_panel(self) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(label("Mini resumos", "SectionTitle"))
        for summary in self.session.summaries:
            layout.addWidget(
                self._origin_tag([summary.block_title]),
                alignment=Qt.AlignmentFlag.AlignLeft,
            )
            viewer = QTextBrowser()
            viewer.setMarkdown(summary.text)
            viewer.setMaximumHeight(150)
            layout.addWidget(viewer)
        return card

    def _flashcards_panel(self) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(label("Flashcards", "SectionTitle"))
        for flashcard in self.session.flashcards:
            layout.addWidget(
                self._origin_tag(self._origin_titles(flashcard.origins)),
                alignment=Qt.AlignmentFlag.AlignLeft,
            )
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
        layout.addWidget(label("Perguntas", "SectionTitle"))
        for question in self.session.questions:
            layout.addWidget(
                self._origin_tag(self._origin_titles(question.origins)),
                alignment=Qt.AlignmentFlag.AlignLeft,
            )
            layout.addWidget(label(question.statement, "SmallTitle"))
            buttons: dict[str, QPushButton] = {}
            for letter in ("A", "B", "C", "D"):
                if letter not in question.alternatives:
                    continue
                button = QPushButton(f"{letter}) {question.alternatives.get(letter, '')}")
                button.setObjectName("GhostButton")
                button.clicked.connect(
                    lambda checked=False, item=question, selected=letter, group=buttons: (
                        self._select_answer(item, selected, group)
                    )
                )
                buttons[letter] = button
                layout.addWidget(button)
            feedback = label("", "Muted")
            answer = QPushButton("Responder")
            answer.setObjectName("PrimaryButton")
            answer.clicked.connect(
                lambda checked=False,
                item=question,
                message=feedback,
                group=buttons,
                action=answer: self._submit_answer(item, message, group, action)
            )
            layout.addWidget(answer)
            layout.addWidget(feedback)
        return card

    def _rate_card(self, flashcard: CombinedFlashcardDTO, status: str) -> None:
        for origin in flashcard.origins:
            self.review_flashcard_use_case.execute(origin.block_id, origin.item_id, status)
        show_toast(self, "Flashcard registrado em todos os blocos de origem.", "success")

    def _question_key(self, question: CombinedQuestionDTO) -> str:
        return "|".join(f"{origin.block_id}:{origin.item_id}" for origin in question.origins)

    def _select_answer(
        self,
        question: CombinedQuestionDTO,
        selected: str,
        buttons: dict[str, QPushButton],
    ) -> None:
        self.selected_answers[self._question_key(question)] = selected
        for letter, button in buttons.items():
            button.setStyleSheet(
                f"border-color: {COLORS['accent']}; background: {COLORS['accent_dark']};"
                if letter == selected
                else ""
            )

    def _submit_answer(
        self,
        question: CombinedQuestionDTO,
        feedback: QLabel,
        buttons: dict[str, QPushButton],
        action: QPushButton,
    ) -> None:
        selected = self.selected_answers.get(self._question_key(question))
        if not selected:
            show_toast(self, "Selecione uma alternativa antes de responder.", "warning")
            return
        for origin in question.origins:
            self.answer_question_use_case.execute(
                origin.block_id,
                origin.item_id,
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

    def _complete(self) -> None:
        for block in self.session.blocks:
            self.study_session_query_service.record_access(block.block_id)
        log_action(
            "combined_review_completed",
            block_ids=",".join(block.block_id for block in self.session.blocks),
        )
        self.accept()

    def _skip(self) -> None:
        log_action(
            "combined_review_skipped",
            block_ids=",".join(block.block_id for block in self.session.blocks),
        )
        self.reject()

    def _origin_titles(self, origins: list[CombinedReviewOriginDTO]) -> list[str]:
        return list(dict.fromkeys(origin.block_title for origin in origins))

    def _origin_tag(self, titles: list[str]) -> QLabel:
        item = label(f"Origem: {' + '.join(titles)}", "ReviewOriginTag")
        item.setWordWrap(False)
        return item
