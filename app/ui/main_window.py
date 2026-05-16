from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.application.query_services.search_query_service import SearchQueryService
from app.application.query_services.ui_data_provider import UIDataProvider
from app.core.database import SQLiteStorage
from app.ui.components.sidebar import Sidebar
from app.ui.components.toast import Toast
from app.ui.components.topbar import TopBar
from app.ui.feedback import log_action
from app.ui.pages.database_page import DatabasePage
from app.ui.pages.flashcards_page import FlashcardsPage
from app.ui.pages.home_page import HomePage
from app.ui.pages.import_page import ImportPage
from app.ui.pages.progress_page import ProgressPage
from app.ui.pages.questions_page import QuestionsPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.studies_page import StudiesPage
from app.ui.pages.subjects_page import SubjectsPage
from app.ui.theme import apply_app_theme_settings, polish_combo_box


class SearchResultsDialog(QDialog):
    def __init__(self, query: str, results: list[tuple[str, str, dict[str, str]]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Busca global")
        self.resize(720, 480)
        self.selected_target: dict[str, str] | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(QLabel(f"Resultados para: {query}"))
        self.list_widget = QListWidget()
        for title, subtitle, target in results:
            item = QListWidgetItem(f"{title}\n{subtitle}")
            item.setData(Qt.ItemDataRole.UserRole, target)
            self.list_widget.addItem(item)
        self.list_widget.itemDoubleClicked.connect(self._open_item)
        layout.addWidget(self.list_widget, 1)

        actions = QHBoxLayout()
        actions.addStretch()
        cancel = QPushButton("Fechar")
        open_button = QPushButton("Abrir selecionado")
        open_button.setObjectName("PrimaryButton")
        cancel.clicked.connect(self.reject)
        open_button.clicked.connect(self._open_selected)
        actions.addWidget(cancel)
        actions.addWidget(open_button)
        layout.addLayout(actions)

    def _open_selected(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            return
        self.selected_target = dict(item.data(Qt.ItemDataRole.UserRole))
        self.accept()

    def _open_item(self, item: QListWidgetItem) -> None:
        self.selected_target = dict(item.data(Qt.ItemDataRole.UserRole))
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LearnKit")
        self.resize(1440, 900)
        self.storage = SQLiteStorage("data/learnkit.db")
        self._apply_saved_theme()
        self.provider = UIDataProvider(self.storage)
        self.search_query_service = SearchQueryService(self.storage)
        self.subjects = self.provider.subjects()
        self.subject_filter = "Todas as matérias"
        self._search_targets: dict[str, dict[str, str]] = {}
        log_action("app_started")

        central = QWidget()
        central.setObjectName("RootWindow")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.page_selected.connect(self.navigate)
        root.addWidget(self.sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.topbar = TopBar(self.subjects)
        self.topbar.search_submitted.connect(self.search_global)
        self.topbar.search_changed.connect(self.update_search_suggestions)
        self.topbar.search_suggestion_selected.connect(self.open_search_suggestion)
        self.topbar.subject_changed.connect(self.apply_subject_filter)
        content_layout.addWidget(self.topbar)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack, 1)
        root.addWidget(content, 1)

        self.pages = {
            "home": HomePage(self.provider),
            "subjects": SubjectsPage(self.provider),
            "studies": StudiesPage(self.provider, self.storage),
            "flashcards": FlashcardsPage(self.provider, self.storage),
            "questions": QuestionsPage(self.provider, self.storage),
            "progress": ProgressPage(self.provider, self.storage),
            "database": DatabasePage(self.storage),
            "import": ImportPage(self.subjects, self.storage),
            "settings": SettingsPage(self.storage),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)
        self.toast = Toast(self)
        self.statusBar().showMessage("LearnKit pronto.", 2500)
        self.navigate("home")

    def show_toast(self, message: str, kind: str = "info") -> None:
        log_action("toast", kind=kind, message=message)
        self.toast.show_message(message, kind)

    def confirm_action(self, title: str, message: str) -> bool:
        log_action("confirm_action", title=title)
        return QMessageBox.question(self, title, message) == QMessageBox.StandardButton.Yes

    def navigate(self, key: str) -> None:
        self.subjects = self.provider.subjects()
        self.topbar.refresh_subjects(self.subjects)
        page = self.pages.get(key)
        if page is None:
            self.show_toast(f"Pagina desconhecida: {key}", "warning")
            return
        if hasattr(page, "set_subject_filter"):
            page.set_subject_filter(self.subject_filter)
        if hasattr(page, "refresh"):
            page.refresh()
        self.sidebar.set_active(key)
        self.stack.setCurrentWidget(page)
        self._polish_interactive_widgets()
        log_action("page_opened", page=key)

    def apply_subject_filter(self, subject_name: str) -> None:
        self.subject_filter = subject_name or "Todas as matérias"
        page = self.stack.currentWidget()
        if hasattr(page, "set_subject_filter"):
            page.set_subject_filter(self.subject_filter)
        elif self.subject_filter != "Todas as matérias" and hasattr(page, "select_subject_by_name"):
            page.select_subject_by_name(self.subject_filter)
        if hasattr(page, "refresh"):
            page.refresh()
        self._polish_interactive_widgets()
        self.show_toast(f"Filtro de materia: {self.subject_filter}", "info")
        log_action("subject_filter_changed", subject=self.subject_filter)

    def update_search_suggestions(self, query: str) -> None:
        query = query.strip()
        self._search_targets = {}
        if len(query) < 2:
            self.topbar.set_search_suggestions([])
            return
        displays: list[str] = []
        for title, subtitle, target in self._collect_search_results(query)[:12]:
            display = f"{subtitle} • {title}"
            while display in self._search_targets:
                display += " "
            self._search_targets[display] = target
            displays.append(display)
        self.topbar.set_search_suggestions(displays)

    def open_search_suggestion(self, display: str) -> None:
        target = self._search_targets.get(display)
        if target:
            self.open_search_target(target)
            self.topbar.search.clear()

    def search_global(self, query: str) -> None:
        query = query.strip()
        if not query:
            self.show_toast("Digite um termo para buscar.", "warning")
            return
        results = self._collect_search_results(query)
        log_action("global_search", query=query, results=len(results))
        if not results:
            self.show_toast("Nenhum resultado encontrado.", "info")
            return
        dialog = SearchResultsDialog(query, results, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_target:
            self.open_search_target(dialog.selected_target)

    def open_search_target(self, target: dict[str, str]) -> None:
        kind = target.get("kind", "")
        if kind == "subject":
            self.open_subject(target["subject"])
        elif kind == "module":
            self.open_subject(target["subject"], target.get("module"))
        elif kind == "block":
            self.open_block(target["block_id"], "studies")
        elif kind == "flashcard":
            self.open_block(target["block_id"], "flashcards")
        elif kind == "question":
            self.open_block(target["block_id"], "questions")
        log_action("search_result_opened", kind=kind)

    def open_subject(self, subject_name: str, module_name: str | None = None) -> None:
        self.navigate("subjects")
        page = self.pages["subjects"]
        if hasattr(page, "select_subject_by_name"):
            page.select_subject_by_name(subject_name, module_name)

    def open_block(self, block_id: str, destination: str = "studies") -> None:
        self.navigate(destination)
        page = self.pages.get(destination)
        if page is not None and hasattr(page, "select_block_by_id"):
            page.select_block_by_id(block_id)

    def _collect_search_results(self, query: str) -> list[tuple[str, str, dict[str, str]]]:
        return self.search_query_service.search(query, limit=50)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if hasattr(self, "toast"):
            self.toast.reposition()

    def _polish_interactive_widgets(self) -> None:
        for button in self.findChildren(QAbstractButton):
            button.setCursor(
                Qt.CursorShape.PointingHandCursor
                if button.isEnabled()
                else Qt.CursorShape.ArrowCursor
            )
        for combo in self.findChildren(QComboBox):
            combo.setCursor(Qt.CursorShape.PointingHandCursor)
            combo.view().setCursor(Qt.CursorShape.PointingHandCursor)
            polish_combo_box(combo)

    def _apply_saved_theme(self) -> None:
        settings_path = self.storage.base_path / "settings.json"
        if not settings_path.exists():
            return
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        if isinstance(settings, dict):
            app = QApplication.instance()
            if app is not None:
                apply_app_theme_settings(app, settings)

