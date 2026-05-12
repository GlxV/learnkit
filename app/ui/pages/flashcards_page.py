from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from app.core.models.flashcard import Flashcard
from app.core.models.study_block import StudyBlock
from app.core.services.progress_service import ProgressService
from app.core.storage.local_storage import LocalStorage
from app.ui.components.cards import EmptyState, FlashcardViewer, ProgressLine, label
from app.ui.feedback import log_action, show_toast
from app.ui.mock_data import UIBlock, UIDataProvider, UIModule, UISubject
from app.ui.pages.base import panel, scroll_page


class FlashcardsPage(QWidget):
    def __init__(self, provider: UIDataProvider, storage: LocalStorage) -> None:
        super().__init__()
        self.provider = provider
        self.storage = storage
        self.progress_service = ProgressService(storage)
        self.subjects = provider.subjects()
        self.current_block: StudyBlock | None = None
        self.cards: list[Flashcard] = []
        self.current_index = 0
        self.session_queue: list[int] = []
        self.queue_position = 0
        self.viewer: FlashcardViewer | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll, _, self.layout = scroll_page()
        root.addWidget(scroll)
        self._build()

    def refresh(self) -> None:
        self._clear_layout(self.layout)
        self.subjects = self.provider.subjects()
        self.current_block = None
        self.cards = []
        self.current_index = 0
        self.session_queue = []
        self.queue_position = 0
        self.viewer = None
        self._build()

    def _build(self) -> None:
        self.layout.addWidget(label("Flashcards", "Title"))
        if not [block for block in self.provider.all_blocks() if block.flashcards]:
            self.layout.addWidget(
                EmptyState(
                    "Nenhum flashcard disponivel.",
                    "Importe uma resposta da IA em um bloco para comecar a revisar flashcards reais.",
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
        first = next((block for block in self.provider.all_blocks() if block.flashcards), None)
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
                if block.flashcards > 0:
                    self.block_combo.addItem(block.title, block.id)
        self._load_selected_block()

    def _load_selected_block(self) -> None:
        block_id = self.block_combo.currentData()
        if not block_id:
            return
        _, _, block = self.storage.get_block_by_id(block_id)
        self.current_block = block
        self.cards = block.flashcards
        self.current_index = 0
        self.session_queue = list(range(len(self.cards)))
        self.queue_position = 0
        self._render_session()

    def _render_session(self) -> None:
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        if not self.current_block or not self.cards:
            self.body.addWidget(
                EmptyState(
                    "Este bloco ainda nao possui flashcards.",
                    "Importe uma resposta da IA para criar cards de revisao.",
                )
            )
            return

        left = panel()
        left.setFixedWidth(300)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.addWidget(label("Blocos com flashcards", "SectionTitle"))
        for block in self.provider.all_blocks():
            if block.flashcards:
                row = QPushButton(f"{block.title}\n{block.flashcards} cards")
                row.setObjectName("GhostButton")
                row.clicked.connect(lambda checked=False, item=block: self._select_block(item))
                left_layout.addWidget(row)
        left_layout.addStretch()

        center = QVBoxLayout()
        self.current_index = self.session_queue[self.queue_position] if self.session_queue else 0
        card = self.cards[self.current_index]
        self.viewer = FlashcardViewer(card.question, card.answer)
        center.addWidget(self.viewer)
        controls = QHBoxLayout()
        for text, handler, style in [
            ("Anterior", self._previous, ""),
            ("Repetir", lambda: self._mark("again"), "danger"),
            ("Dificil", lambda: self._mark("hard"), "warning"),
            ("Bom", lambda: self._mark("good"), "good"),
            ("Dominei", lambda: self._mark("easy"), "primary"),
            ("Pular", lambda: self._mark("skipped"), ""),
        ]:
            button = QPushButton(text)
            if style == "primary":
                button.setObjectName("PrimaryButton")
            elif style == "warning":
                button.setStyleSheet("border-color: #F59E0B; color: #F59E0B;")
            elif style == "danger":
                button.setStyleSheet("border-color: #EF4444; color: #EF4444;")
            elif style == "good":
                button.setStyleSheet("border-color: #22C55E; color: #22C55E;")
            button.clicked.connect(handler)
            controls.addWidget(button)
        center.addLayout(controls)
        center.addWidget(
            label(
                "Repetir volta logo. Dificil reaparece depois. Bom segue. Dominei conclui o card.",
                "Weak",
            )
        )

        right = panel()
        right.setFixedWidth(280)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 16, 16, 16)
        progress = self.progress_service.get_block_progress(self.current_block.id)
        right_layout.addWidget(label("Sua sessao", "SectionTitle"))
        right_layout.addWidget(label(f"Fila: {self.queue_position + 1} de {len(self.session_queue)}", "Muted"))
        right_layout.addWidget(label(f"Card real: {self.current_index + 1} de {len(self.cards)}", "Weak"))
        right_layout.addWidget(ProgressLine(int((progress.flashcards_reviewed / max(1, progress.flashcards_total)) * 100)))
        right_layout.addWidget(label(f"Revisados: {progress.flashcards_reviewed}", "Muted"))
        right_layout.addWidget(label(f"Repetir: {progress.flashcards_again}", "Muted"))
        right_layout.addWidget(label(f"Bons: {progress.flashcards_good}", "Muted"))
        right_layout.addWidget(label(f"Dominados: {progress.flashcards_mastered}", "Muted"))
        right_layout.addWidget(label(f"Dificeis: {progress.flashcards_difficult}", "Muted"))
        right_layout.addStretch()

        self.body.addWidget(left)
        self.body.addLayout(center, 1)
        self.body.addWidget(right)

    def _select_block(self, block: UIBlock) -> None:
        if block.id:
            index = self.block_combo.findData(block.id)
            if index >= 0:
                self.block_combo.setCurrentIndex(index)

    def _mark(self, status: str) -> None:
        if not self.current_block or not self.cards:
            return
        card = self.cards[self.current_index]
        if status != "skipped":
            self.progress_service.record_flashcard(self.current_block.id, card.id, status)
        self._schedule_after_rating(status, self.current_index)
        labels = {
            "again": "Repetir",
            "hard": "Dificil",
            "good": "Bom",
            "easy": "Dominei",
            "skipped": "Pulou",
        }
        show_toast(self, f"Flashcard: {labels.get(status, status)}.", "success")
        log_action("flashcard_marked", block_id=self.current_block.id, flashcard_id=card.id, status=status)
        self._advance()

    def _schedule_after_rating(self, status: str, card_index: int) -> None:
        future = self.session_queue[self.queue_position + 1 :]
        self.session_queue = self.session_queue[: self.queue_position + 1] + [
            item for item in future if item != card_index
        ]
        if status == "again":
            insert_at = min(self.queue_position + 2, len(self.session_queue))
            self.session_queue.insert(insert_at, card_index)
        elif status == "hard":
            insert_at = min(self.queue_position + 4, len(self.session_queue))
            self.session_queue.insert(insert_at, card_index)

    def _previous(self) -> None:
        if self.session_queue:
            self.queue_position = max(0, self.queue_position - 1)
            self._render_session()

    def _next(self) -> None:
        self._advance()

    def _advance(self) -> None:
        if self.session_queue:
            if self.queue_position >= len(self.session_queue) - 1:
                show_toast(self, "Fim da fila de revisao deste bloco.", "info")
            else:
                self.queue_position += 1
            self._render_session()

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
