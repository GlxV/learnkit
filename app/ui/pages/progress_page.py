from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from app.core.services.progress_service import ProgressService
from app.core.storage.local_storage import LocalStorage
from app.ui.components.cards import EmptyState, ProgressLine, StatCard, label
from app.ui.components.progress_ring import ProgressRing
from app.ui.mock_data import UIDataProvider, UISubject
from app.ui.pages.base import panel, scroll_page
from app.ui.theme import COLORS


class ProgressPage(QWidget):
    def __init__(self, provider: UIDataProvider, storage: LocalStorage) -> None:
        super().__init__()
        self.provider = provider
        self.storage = storage
        self.progress_service = ProgressService(storage)
        self.subject_filter = "Todas as matérias"
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll, _, self.layout = scroll_page()
        root.addWidget(scroll)
        self.refresh()

    def refresh(self) -> None:
        self._clear_layout(self.layout)
        subjects = self.provider.subjects()
        if self.subject_filter != "Todas as matérias":
            subjects = [subject for subject in subjects if subject.name == self.subject_filter]
        stats = self.provider.global_stats() if self.subject_filter == "Todas as matérias" else self._stats_for_subjects(subjects)

        self.layout.addWidget(label("Progresso", "Title"))
        self.layout.addWidget(label("Estatísticas calculadas a partir dos blocos salvos localmente.", "Muted"))

        cards = QGridLayout()
        cards.setHorizontalSpacing(12)
        top_cards = [
            StatCard("Progresso geral", f"{stats.progress_percent}%", "cards + perguntas", "activity", COLORS["blue"]),
            StatCard("Tempo total", f"{stats.study_time_seconds // 60} min", "registrado", "clock", COLORS["purple_soft"]),
            StatCard("Perguntas", str(stats.questions_answered), "respondidas", "questions", "#EC4899"),
            StatCard("Acertos", str(stats.questions_correct), "questões corretas", "check", COLORS["green"]),
            StatCard("Flashcards", str(stats.flashcards_reviewed), "revisados", "flashcards", COLORS["amber"]),
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
        grid.addWidget(self._overview_panel(stats.progress_percent, stats.total_flashcards, stats.total_questions), 0, 0)
        grid.addWidget(self._subjects_panel(subjects), 0, 1)
        grid.addWidget(self._module_panel(subjects), 1, 0)
        grid.addWidget(self._accuracy_panel(stats.questions_correct, stats.questions_wrong), 1, 1)
        self.layout.addLayout(grid)

    def set_subject_filter(self, subject_name: str) -> None:
        self.subject_filter = subject_name or "Todas as matérias"

    def _stats_for_subjects(self, subjects):
        from app.core.models.progress import AggregateProgress

        aggregate = AggregateProgress(total_subjects=len(subjects))
        for subject in subjects:
            aggregate.total_modules += len(subject.modules)
            for module in subject.modules:
                aggregate.total_blocks += len(module.blocks)
                for block in module.blocks:
                    if not block.id:
                        continue
                    progress = self.progress_service.get_block_progress(block.id)
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

    def _overview_panel(self, percent: int, total_cards: int, total_questions: int) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        layout.addWidget(label("Visão geral", "SectionTitle"))
        row = QHBoxLayout()
        row.addWidget(ProgressRing(percent, 132))
        details = QVBoxLayout()
        details.addWidget(label(f"Flashcards cadastrados: {total_cards}", "Muted"))
        details.addWidget(label(f"Perguntas cadastradas: {total_questions}", "Muted"))
        details.addWidget(label("A porcentagem sobe quando você revisa cards ou responde perguntas.", "Weak"))
        row.addLayout(details, 1)
        layout.addLayout(row)
        layout.addWidget(ProgressLine(percent))
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
            row.addWidget(label(f"{subject.progress}%", "Muted"))
            layout.addLayout(row)
            layout.addWidget(ProgressLine(subject.progress))
        layout.addStretch()
        return card

    def _module_panel(self, subjects: list[UISubject]) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(label("Conclusão por módulo", "SectionTitle"))
        modules = [module for subject in subjects for module in subject.modules]
        if not modules:
            layout.addWidget(label("Nenhum módulo criado ainda.", "Muted"))
            return card
        for module in modules[:8]:
            row = QHBoxLayout()
            row.addWidget(label(module.name, "SmallTitle"), 1)
            row.addWidget(label(f"{len(module.blocks)} blocos", "Weak"))
            row.addWidget(label(f"{module.progress}%", "Muted"))
            layout.addLayout(row)
            layout.addWidget(ProgressLine(module.progress))
        return card

    def _accuracy_panel(self, correct: int, wrong: int) -> QWidget:
        total = correct + wrong
        percent = int((correct / total) * 100) if total else 0
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        layout.addWidget(label("Precisão nas perguntas", "SectionTitle"))
        row = QHBoxLayout()
        row.addWidget(ProgressRing(percent, 118))
        details = QVBoxLayout()
        details.addWidget(label(f"Acertos: {correct}", "Muted"))
        details.addWidget(label(f"Erros: {wrong}", "Muted"))
        details.addWidget(label("Sem respostas registradas ainda." if not total else "Baseado nas perguntas respondidas.", "Weak"))
        row.addLayout(details, 1)
        layout.addLayout(row)
        return card

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
