from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from app.application.dto.progress import (
    ReviewActivityDTO,
    ReviewDashboardBlockDTO,
    ReviewDashboardSummaryDTO,
)
from app.application.query_services.dashboard_query_service import DashboardQueryService
from app.application.query_services.progress_query_service import ProgressQueryService
from app.application.query_services.ui_data_provider import UIDataProvider, UISubject
from app.core.models.progress import AggregateProgress
from app.core.storage.local_storage import LocalStorage
from app.ui.components.cards import EmptyState, ProgressLine, StatCard, label
from app.ui.components.progress_ring import ProgressRing
from app.ui.pages.base import panel, scroll_page
from app.ui.theme import COLORS


ALL_SUBJECTS = "Todas as matérias"


class ProgressPage(QWidget):
    def __init__(self, provider: UIDataProvider, storage: LocalStorage) -> None:
        super().__init__()
        self.provider = provider
        self.storage = storage
        self.progress_query_service = ProgressQueryService(storage)
        self.dashboard_query_service = DashboardQueryService(storage)
        self.subject_filter = ALL_SUBJECTS
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll, _, self.layout = scroll_page()
        root.addWidget(scroll)
        self.refresh()

    def refresh(self) -> None:
        self._clear_layout(self.layout)
        subjects = self._filtered_subjects()
        stats = self.provider.global_stats() if self.subject_filter == ALL_SUBJECTS else self._stats_for_subjects(subjects)
        dashboard = self.dashboard_query_service.review_dashboard_dto(
            None if self.subject_filter == ALL_SUBJECTS else self.subject_filter
        )
        summary = dashboard.summary

        self.layout.addWidget(label("Progresso", "Title"))
        self.layout.addWidget(
            label(
                "Acompanhe progresso real, revisões pendentes e atividade salva no SQLite.",
                "Muted",
            )
        )

        cards = QGridLayout()
        cards.setHorizontalSpacing(12)
        top_cards = [
            StatCard("Progresso geral", f"{stats.progress_percent}%", "cards + perguntas", "activity", COLORS["blue"]),
            StatCard("Pendências", str(summary.pending_reviews), "revisar agora", "progress", COLORS["purple_soft"]),
            StatCard("Cards vencidos", str(summary.due_flashcards), "fila de revisão", "flashcards", COLORS["amber"]),
            StatCard("Perguntas erradas", str(summary.wrong_questions), "corrigir depois", "questions", "#EC4899"),
            StatCard("Atividade", str(len(dashboard.activity)), "eventos recentes", "activity", COLORS["green"]),
        ]
        for index, card in enumerate(top_cards):
            cards.addWidget(card, 0, index)
        self.layout.addLayout(cards)

        if not subjects:
            empty = EmptyState("Nenhum progresso ainda.", "Crie uma matéria e importe conteúdo para começar.")
            empty_layout = empty.layout()
            if empty_layout is not None:
                button = QPushButton("Importar conteúdo")
                button.setObjectName("PrimaryButton")
                button.clicked.connect(lambda: self._navigate("import"))
                empty_layout.addWidget(button)
            self.layout.addWidget(empty)
            self.layout.addStretch()
            return

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        grid.addWidget(self._overview_panel(stats, summary), 0, 0)
        grid.addWidget(self._review_focus_panel(summary), 0, 1)
        grid.addWidget(self._blocks_panel(dashboard.blocks), 1, 0)
        grid.addWidget(self._activity_panel(dashboard.activity), 1, 1)
        grid.addWidget(self._subjects_panel(subjects), 2, 0, 1, 2)
        self.layout.addLayout(grid)

    def set_subject_filter(self, subject_name: str) -> None:
        self.subject_filter = subject_name or ALL_SUBJECTS

    def _filtered_subjects(self) -> list[UISubject]:
        subjects = self.provider.subjects()
        if self.subject_filter != ALL_SUBJECTS:
            subjects = [subject for subject in subjects if subject.name == self.subject_filter]
        return subjects

    def _stats_for_subjects(self, subjects: list[UISubject]) -> AggregateProgress:
        aggregate = AggregateProgress(total_subjects=len(subjects))
        for subject in subjects:
            aggregate.total_modules += len(subject.modules)
            for module in subject.modules:
                aggregate.total_blocks += len(module.blocks)
                for block in module.blocks:
                    if not block.id:
                        continue
                    progress = self.progress_query_service.block_progress(block.id)
                    aggregate.total_flashcards += progress.flashcards_total
                    aggregate.total_questions += progress.questions_total
                    aggregate.flashcards_reviewed += progress.flashcards_reviewed
                    aggregate.questions_answered += progress.questions_answered
                    aggregate.questions_correct += progress.questions_correct
                    aggregate.questions_wrong += progress.questions_wrong
                    aggregate.study_time_seconds += progress.study_time_seconds
        total = aggregate.total_flashcards + aggregate.total_questions
        done = aggregate.flashcards_reviewed + aggregate.questions_answered
        aggregate.progress_percent = int((done / total) * 100) if total else 0
        return aggregate

    def _overview_panel(self, stats: AggregateProgress, summary: ReviewDashboardSummaryDTO) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        layout.addWidget(label("Visão geral", "SectionTitle"))
        row = QHBoxLayout()
        row.addWidget(ProgressRing(stats.progress_percent, 132))
        details = QVBoxLayout()
        details.addWidget(label(f"Flashcards cadastrados: {stats.total_flashcards}", "Muted"))
        details.addWidget(label(f"Perguntas cadastradas: {stats.total_questions}", "Muted"))
        details.addWidget(label(f"Cards novos: {summary.new_flashcards}", "Muted"))
        details.addWidget(label(f"Perguntas não respondidas: {summary.unanswered_questions}", "Muted"))
        details.addWidget(label("A porcentagem sobe quando você revisa cards ou responde perguntas.", "Weak"))
        row.addLayout(details, 1)
        layout.addLayout(row)
        layout.addWidget(ProgressLine(stats.progress_percent))
        return card

    def _review_focus_panel(self, summary: ReviewDashboardSummaryDTO) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(label("Fila de revisão", "SectionTitle"))
        rows = [
            ("Cards vencidos", summary.due_flashcards, COLORS["amber"], "flashcards"),
            ("Cards novos", summary.new_flashcards, COLORS["blue"], "flashcards"),
            ("Perguntas erradas", summary.wrong_questions, "#EC4899", "questions"),
            ("Perguntas em branco", summary.unanswered_questions, COLORS["purple_soft"], "questions"),
        ]
        for title, value, color, destination in rows:
            row = QHBoxLayout()
            row.addWidget(label(title, "SmallTitle"), 1)
            count = label(str(value), "Muted")
            count.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: 800;")
            row.addWidget(count)
            button = QPushButton("Abrir")
            button.setObjectName("GhostButton")
            button.clicked.connect(lambda checked=False, key=destination: self._navigate(key))
            row.addWidget(button)
            layout.addLayout(row)
        return card

    def _blocks_panel(self, blocks: list[ReviewDashboardBlockDTO]) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(label("Prioridade por bloco", "SectionTitle"))
        if not blocks:
            layout.addWidget(label("Nenhum bloco com progresso registrado ainda.", "Muted"))
            return card
        for item in blocks[:8]:
            row = QHBoxLayout()
            text = QVBoxLayout()
            text.addWidget(label(item.block_title, "SmallTitle"))
            text.addWidget(label(f"{item.subject_name} > {item.module_name}", "Weak"))
            row.addLayout(text, 1)
            pending = label(f"{item.pending_reviews} pend.", "Muted")
            pending.setStyleSheet(f"color: {COLORS['amber']}; font-weight: 800;")
            row.addWidget(pending)
            flash_button = QPushButton("Cards")
            flash_button.setObjectName("GhostButton")
            flash_button.clicked.connect(
                lambda checked=False, block_id=item.block_id: self._open_block(block_id, "flashcards")
            )
            questions_button = QPushButton("Perguntas")
            questions_button.setObjectName("GhostButton")
            questions_button.clicked.connect(
                lambda checked=False, block_id=item.block_id: self._open_block(block_id, "questions")
            )
            row.addWidget(flash_button)
            row.addWidget(questions_button)
            layout.addLayout(row)
            layout.addWidget(ProgressLine(item.progress_percent))
        return card

    def _activity_panel(self, activity: list[ReviewActivityDTO]) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(label("Atividade recente", "SectionTitle"))
        if not activity:
            layout.addWidget(label("A atividade aparece aqui depois que você estudar flashcards ou perguntas.", "Muted"))
            return card
        for item in activity[:10]:
            row = QVBoxLayout()
            row.addWidget(label(item.title, "SmallTitle"))
            row.addWidget(
                label(
                    f"{item.detail} • {item.block_title} • {self._date(item.occurred_at)}",
                    "Weak",
                )
            )
            layout.addLayout(row)
        return card

    def _subjects_panel(self, subjects: list[UISubject]) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(label("Progresso por matéria", "SectionTitle"))
        for subject in subjects:
            row = QHBoxLayout()
            row.addWidget(label(subject.name, "SmallTitle"), 1)
            row.addWidget(label(f"{len(subject.modules)} módulos", "Weak"))
            row.addWidget(label(f"{subject.progress}%", "Muted"))
            layout.addLayout(row)
            layout.addWidget(ProgressLine(subject.progress))
        layout.addStretch()
        return card

    def _date(self, value: object) -> str:
        text = str(value or "")
        return text.split("T", 1)[0] if text else "sem data"

    def _open_block(self, block_id: str, destination: str) -> None:
        window = self.window()
        if hasattr(window, "open_block"):
            window.open_block(block_id, destination)
            return
        self._navigate(destination)

    def _navigate(self, key: str) -> None:
        window = self.window()
        if hasattr(window, "navigate"):
            window.navigate(key)

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

