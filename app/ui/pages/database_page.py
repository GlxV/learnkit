from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.database import SQLiteStorage
from app.ui.components.cards import EmptyState, StatCard, label
from app.ui.components.visual import GlassPanel
from app.ui.feedback import log_action, show_toast
from app.ui.pages.base import scroll_page


class DatabasePage(QWidget):
    def __init__(self, storage: SQLiteStorage) -> None:
        super().__init__()
        self.storage = storage

        scroll, _content, layout = scroll_page()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Banco de Dados")
        title.setObjectName("PageTitle")
        subtitle = label("Demonstração da persistência SQLite usada pelo LearnKit.", "Muted")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)

        self.refresh_button = QPushButton("Atualizar dados")
        self.refresh_button.setObjectName("PrimaryButton")
        self.refresh_button.clicked.connect(lambda: self.refresh(True))
        header.addWidget(self.refresh_button)
        layout.addLayout(header)

        info = GlassPanel()
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(20, 18, 20, 18)
        info_layout.setSpacing(8)
        info_layout.addWidget(label("Arquivo SQLite", "SectionTitle"))
        self.db_path = label("", "Muted")
        self.db_status = label("", "Weak")
        self.db_path.setTextInteractionFlags(self.db_path.textInteractionFlags() | self.db_path.textInteractionFlags())
        info_layout.addWidget(self.db_path)
        info_layout.addWidget(self.db_status)
        layout.addWidget(info)

        self.stats_grid = QGridLayout()
        self.stats_grid.setHorizontalSpacing(14)
        self.stats_grid.setVerticalSpacing(14)
        layout.addLayout(self.stats_grid)

        recent_panel = GlassPanel()
        recent_layout = QVBoxLayout(recent_panel)
        recent_layout.setContentsMargins(20, 18, 20, 18)
        recent_layout.setSpacing(12)
        recent_layout.addWidget(label("Últimos registros criados", "SectionTitle"))
        self.recent_list = QListWidget()
        self.recent_list.setObjectName("AuditList")
        recent_layout.addWidget(self.recent_list)
        layout.addWidget(recent_panel, 1)

        self.empty = EmptyState(
            "Nenhum dado salvo ainda.",
            "Crie uma matéria, módulo ou bloco e volte aqui para ver os contadores mudarem.",
        )
        layout.addWidget(self.empty)
        self.empty.hide()
        self.refresh(notify=False)

    def refresh(self, notify: bool = True) -> None:
        stats = self.storage.database_stats()
        db_path = Path(self.storage.db_path)
        self.db_path.setText(str(db_path.resolve()))
        status = "Conectado" if db_path.exists() else "Arquivo ainda não criado"
        self.db_status.setText(f"Status: {status}")

        for index in reversed(range(self.stats_grid.count())):
            item = self.stats_grid.itemAt(index)
            widget = item.widget() if item else None
            if widget is not None:
                widget.deleteLater()

        cards = [
            ("Matérias", stats.get("subjects", 0), "subjects", "registros salvos"),
            ("Módulos", stats.get("modules", 0), "studies", "ligados às matérias"),
            ("Blocos", stats.get("study_blocks", 0), "blocks", "pacotes de estudo"),
            ("Flashcards", stats.get("flashcards", 0), "flashcards", "cartões persistidos"),
            ("Perguntas", stats.get("questions", 0), "questions", "questões persistidas"),
            ("Progresso", stats.get("study_progress", 0), "progress", "linhas de progresso"),
        ]
        for index, (title, value, icon, subtitle) in enumerate(cards):
            self.stats_grid.addWidget(
                StatCard(title, str(value), subtitle, icon=icon),
                index // 3,
                index % 3,
            )

        self.recent_list.clear()
        for record in self.storage.recent_records(16):
            self.recent_list.addItem(
                f"{record.get('kind', 'Registro')}  •  {record.get('title', '')}\n{record.get('created_at', '')}"
            )
        has_data = any(stats.get(key, 0) for key in ("subjects", "modules", "study_blocks"))
        self.empty.setVisible(not has_data)
        log_action("database_page_refreshed", **{key: str(value) for key, value in stats.items()})
        if notify:
            show_toast(self, "Dados do banco atualizados.", "info")
