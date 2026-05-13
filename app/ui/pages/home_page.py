from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.services.progress_service import ProgressService
from app.ui.components.cards import EmptyState, ProgressLine, StatCard, label
from app.ui.components.open_source_panel import OpenSourcePanel
from app.ui.components.progress_ring import ProgressRing
from app.ui.components.visual import GlassPanel, IconBadge
from app.ui.mock_data import UIBlock, UIDataProvider, UIModule, UISubject
from app.ui.pages.base import panel, scroll_page
from app.ui.theme import COLORS


class HomePage(QWidget):
    def __init__(self, provider: UIDataProvider) -> None:
        super().__init__()
        self.provider = provider
        self.progress_service = ProgressService(provider.storage)
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
        blocks = [block for subject in subjects for module in subject.modules for block in module.blocks]
        modules = [module for subject in subjects for module in subject.modules]

        title_box = QVBoxLayout()
        title_box.setSpacing(8)
        title_box.addWidget(label("Visão geral", "Title"))
        title_box.addWidget(label("Acompanhe materiais, revisões e blocos salvos localmente.", "Muted"))
        self.layout.addLayout(title_box)

        self.layout.addLayout(self._stats(subjects))

        if not subjects:
            self.layout.addWidget(self._empty_home())
            self.layout.addStretch()
            return

        body = QHBoxLayout()
        body.setSpacing(18)
        main_col = QVBoxLayout()
        main_col.setSpacing(18)
        side_wrap = QWidget()
        side_wrap.setFixedWidth(360)
        side_col = QVBoxLayout(side_wrap)
        side_col.setContentsMargins(0, 0, 0, 0)
        side_col.setSpacing(14)
        side_col.setAlignment(Qt.AlignmentFlag.AlignTop)
        body.addLayout(main_col, 3)
        body.addWidget(side_wrap)

        main_col.addWidget(self._continue_card(blocks))

        lower = QGridLayout()
        lower.setHorizontalSpacing(12)
        lower.setVerticalSpacing(14)
        lower.setColumnStretch(0, 1)
        lower.setColumnStretch(1, 1)
        lower.setColumnStretch(2, 1)
        lower.addWidget(self._subjects_panel(subjects), 0, 0)
        lower.addWidget(self._modules_panel(modules[:5]), 0, 1)
        lower.addWidget(self._blocks_panel(blocks[:5]), 0, 2)
        main_col.addLayout(lower)

        side_col.addWidget(self._activity_panel(blocks))
        side_col.addWidget(OpenSourcePanel())
        side_col.addWidget(self._progress_panel())
        side_col.addStretch()
        self.layout.addLayout(body)

    def set_subject_filter(self, subject_name: str) -> None:
        self.subject_filter = subject_name or "Todas as matérias"

    def _stats(self, subjects: list[UISubject]) -> QGridLayout:
        stats_data = self.provider.global_stats()
        if self.subject_filter != "Todas as matérias":
            total_modules = sum(len(subject.modules) for subject in subjects)
            total_blocks = sum(len(module.blocks) for subject in subjects for module in subject.modules)
            total_flashcards = sum(block.flashcards for subject in subjects for module in subject.modules for block in module.blocks)
            total_questions = sum(block.questions for subject in subjects for module in subject.modules for block in module.blocks)
            stats_data.total_subjects = len(subjects)
            stats_data.total_modules = total_modules
            stats_data.total_blocks = total_blocks
            stats_data.total_flashcards = total_flashcards
            stats_data.total_questions = total_questions
        stats = QGridLayout()
        stats.setHorizontalSpacing(12)
        cards = [
            StatCard("Matérias", str(stats_data.total_subjects), "dados locais", "subjects", COLORS["blue"]),
            StatCard("Módulos", str(stats_data.total_modules), "criados por você", "activity", COLORS["purple_soft"]),
            StatCard("Blocos", str(stats_data.total_blocks), "pacotes reais", "blocks", "#22D3EE"),
            StatCard(
                "Flashcards",
                str(stats_data.total_flashcards),
                f"{stats_data.flashcards_reviewed} revisados",
                "flashcards",
                COLORS["amber"],
            ),
            StatCard(
                "Perguntas",
                str(stats_data.total_questions),
                f"{stats_data.questions_answered} respondidas",
                "questions",
                "#EC4899",
            ),
        ]
        for index, card in enumerate(cards):
            stats.addWidget(card, 0, index)
        return stats

    def _empty_home(self) -> QWidget:
        card = EmptyState(
            "Nenhuma matéria criada ainda.",
            "Crie uma matéria e importe PDF, PPTX, TXT ou Markdown para gerar o primeiro bloco de estudo.",
        )
        layout = card.layout()
        if layout is not None:
            button = QPushButton("Criar primeira matéria")
            button.setObjectName("PrimaryButton")
            button.clicked.connect(lambda: self._navigate("subjects"))
            layout.addWidget(button)
        return card

    def _continue_card(self, blocks: list[UIBlock]) -> QWidget:
        card = GlassPanel("HeroCard")
        card.setFixedHeight(182)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(label("Continuar estudando", "SectionTitle"))

        if not blocks:
            layout.addWidget(
                label("Você ainda não tem blocos. Importe um material para criar resumo, cards e perguntas.", "Muted")
            )
            action = QPushButton("Importar conteúdo")
            action.setObjectName("PrimaryButton")
            action.clicked.connect(lambda: self._navigate("import"))
            layout.addWidget(action)
            return card

        block = sorted(blocks, key=lambda item: item.progress, reverse=True)[0]
        row = QHBoxLayout()
        row.setSpacing(22)
        preview = QLabel("LK\nstudy")
        preview.setFixedSize(108, 92)
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"stop:0 {COLORS['purple']}, stop:1 #312E81); "
            "border-radius: 12px; font-size: 19px; font-weight: 850; color: white;"
        )
        row.addWidget(preview)

        info = QVBoxLayout()
        info.setSpacing(8)
        info.addWidget(label(block.title, "HeroTitle"))
        info.addWidget(label(f"{block.subject_name} > {block.module_name}", "Muted"))
        info.addWidget(ProgressLine(block.progress))
        meta = QHBoxLayout()
        meta.addWidget(label(f"{block.progress}% concluído", "Weak"))
        meta.addStretch()
        meta.addWidget(label(f"{block.flashcards} cards - {block.questions} perguntas", "Weak"))
        info.addLayout(meta)
        row.addLayout(info, 1)

        actions = QVBoxLayout()
        actions.setSpacing(10)
        continue_button = QPushButton("Continuar")
        continue_button.setObjectName("PrimaryButton")
        continue_button.clicked.connect(lambda: self._open_block(block.id, "studies"))
        flashcards_button = QPushButton("Flashcards")
        flashcards_button.setObjectName("GhostButton")
        flashcards_button.clicked.connect(lambda: self._open_block(block.id, "flashcards"))
        actions.addStretch()
        actions.addWidget(continue_button)
        actions.addWidget(flashcards_button)
        actions.addStretch()
        row.addLayout(actions)
        layout.addLayout(row)
        return card

    def _subjects_panel(self, subjects: list[UISubject]) -> QWidget:
        card = panel()
        card.setMinimumHeight(360)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        header = QHBoxLayout()
        header.addWidget(label("Suas matérias", "SectionTitle"))
        header.addStretch()
        link = QPushButton("Ver todas")
        link.setObjectName("GhostButton")
        link.clicked.connect(lambda: self._navigate("subjects"))
        header.addWidget(link)
        layout.addLayout(header)
        for subject in subjects[:5]:
            layout.addLayout(self._subject_row(subject))
        layout.addStretch()
        return card

    def _modules_panel(self, modules: list[UIModule]) -> QWidget:
        card = panel()
        card.setMinimumHeight(360)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        header = QHBoxLayout()
        header.addWidget(label("Módulos recentes", "SectionTitle"))
        header.addStretch()
        all_button = QPushButton("Ver todos")
        all_button.setObjectName("GhostButton")
        all_button.clicked.connect(lambda: self._navigate("subjects"))
        header.addWidget(all_button)
        layout.addLayout(header)
        if not modules:
            layout.addWidget(label("Nenhum módulo criado ainda.", "Muted"))
            layout.addStretch()
            return card
        for module in modules:
            row = QHBoxLayout()
            badge = IconBadge("M", COLORS["purple"], size=42, radius=10, font_size=14)
            text = QVBoxLayout()
            text.addWidget(label(module.name, "SmallTitle"))
            text.addWidget(label(f"{len(module.blocks)} blocos", "Weak"))
            row.addWidget(badge)
            row.addLayout(text, 1)
            row.addWidget(ProgressRing(module.progress, 42))
            open_button = QPushButton("Abrir")
            open_button.setObjectName("GhostButton")
            open_button.clicked.connect(lambda checked=False, item=module: self._open_module(item))
            row.addWidget(open_button)
            layout.addLayout(row)
        layout.addStretch()
        return card

    def _blocks_panel(self, blocks: list[UIBlock]) -> QWidget:
        card = panel()
        card.setMinimumHeight(360)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        header = QHBoxLayout()
        header.addWidget(label("Últimos blocos", "SectionTitle"))
        header.addStretch()
        all_button = QPushButton("Ver todos")
        all_button.setObjectName("GhostButton")
        all_button.clicked.connect(lambda: self._navigate("studies"))
        header.addWidget(all_button)
        layout.addLayout(header)
        if not blocks:
            layout.addWidget(label("Nenhum bloco importado ainda.", "Muted"))
            layout.addStretch()
            return card
        colors = [COLORS["purple_soft"], COLORS["blue"], COLORS["green"], COLORS["amber"], "#EC4899"]
        for index, block in enumerate(blocks):
            row = QHBoxLayout()
            dot = QLabel()
            dot.setFixedSize(9, 9)
            dot.setStyleSheet(f"background: {colors[index % len(colors)]}; border-radius: 4px;")
            text = QVBoxLayout()
            text.addWidget(label(block.title, "SmallTitle"))
            text.addWidget(label(f"{block.subject_name} > {block.module_name}", "Weak"))
            row.addWidget(dot)
            row.addLayout(text, 1)
            row.addWidget(ProgressRing(block.progress, 42))
            open_button = QPushButton("Abrir")
            open_button.setObjectName("GhostButton")
            open_button.clicked.connect(lambda checked=False, item=block: self._open_block(item.id, "studies"))
            row.addWidget(open_button)
            layout.addLayout(row)
        layout.addStretch()
        return card

    def _activity_panel(self, blocks: list[UIBlock]) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        layout.addWidget(label("Atividade recente", "SectionTitle"))

        items: list[str] = []
        for block in blocks:
            if not block.id:
                continue
            progress = self.progress_service.get_block_progress(block.id)
            if progress.flashcards_reviewed:
                items.append(f"{progress.flashcards_reviewed} flashcards revisados em {block.title}")
            if progress.questions_answered:
                items.append(f"{progress.questions_answered} perguntas respondidas em {block.title}")

        if not items:
            layout.addWidget(label("A atividade aparece aqui depois que você estudar cards ou perguntas.", "Muted"))
            return card

        for item in items[:5]:
            row = QHBoxLayout()
            dot = QLabel()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background: {COLORS['purple_soft']}; border-radius: 5px;")
            row.addWidget(dot)
            row.addWidget(label(item, "Muted"), 1)
            layout.addLayout(row)
        return card

    def _progress_panel(self) -> QWidget:
        stats = self.provider.global_stats()
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        layout.addWidget(label("Seu progresso geral", "SectionTitle"))
        row = QHBoxLayout()
        row.addWidget(ProgressRing(stats.progress_percent, 122))
        details = QVBoxLayout()
        details.addWidget(label(f"Cards revisados: {stats.flashcards_reviewed}/{stats.total_flashcards}", "Muted"))
        details.addWidget(label(f"Perguntas respondidas: {stats.questions_answered}/{stats.total_questions}", "Muted"))
        details.addWidget(label(f"Acertos: {stats.questions_correct}", "Muted"))
        row.addLayout(details, 1)
        layout.addLayout(row)
        layout.addWidget(label(f"Progresso total: {stats.progress_percent}%", "Muted"))
        layout.addWidget(ProgressLine(stats.progress_percent))
        return card

    def _subject_row(self, subject: UISubject) -> QHBoxLayout:
        row = QHBoxLayout()
        badge = IconBadge(subject.icon, subject.color, size=40, radius=10, font_size=15)
        text = QVBoxLayout()
        text.addWidget(label(subject.name, "SmallTitle"))
        text.addWidget(ProgressLine(subject.progress))
        row.addWidget(badge)
        row.addLayout(text, 1)
        row.addWidget(label(f"{subject.progress}%", "Muted"))
        open_button = QPushButton("Abrir")
        open_button.setObjectName("GhostButton")
        open_button.clicked.connect(lambda: self._open_subject(subject.name))
        row.addWidget(open_button)
        return row

    def _open_subject(self, subject_name: str) -> None:
        window = self.window()
        if hasattr(window, "open_subject"):
            window.open_subject(subject_name)
        else:
            self._navigate("subjects")

    def _open_module(self, module: UIModule) -> None:
        subject_name = self.subject_filter if self.subject_filter != "Todas as matérias" else None
        if not subject_name:
            for subject in self.provider.subjects():
                if any(item.name == module.name for item in subject.modules):
                    subject_name = subject.name
                    break
        window = self.window()
        if subject_name and hasattr(window, "open_subject"):
            window.open_subject(subject_name, module.name)
        else:
            self._navigate("subjects")

    def _open_block(self, block_id: str | None, destination: str) -> None:
        window = self.window()
        if block_id and hasattr(window, "open_block"):
            window.open_block(block_id, destination)
        else:
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
