from __future__ import annotations

from PySide6.QtCore import QStringListModel, Qt, Signal
from PySide6.QtWidgets import QCompleter, QFrame, QHBoxLayout, QLineEdit

from app.ui.components.icons import LineIcon
from app.ui.components.subject_selector import SubjectSelector
from app.application.query_services.ui_data_provider import UISubject


class TopBar(QFrame):
    subject_changed = Signal(str)
    search_submitted = Signal(str)
    search_changed = Signal(str)
    search_suggestion_selected = Signal(str)

    def __init__(self, subjects: list[UISubject]) -> None:
        super().__init__()
        self.setObjectName("Topbar")
        self.setFixedHeight(72)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 12, 28, 12)
        layout.setSpacing(14)

        search_box = QFrame()
        search_box.setObjectName("SearchBox")
        search_layout = QHBoxLayout(search_box)
        search_layout.setContentsMargins(14, 0, 14, 0)
        search_layout.setSpacing(10)
        search_layout.addWidget(LineIcon("search", "#9BA8BA", 22))
        self.search = QLineEdit()
        self.search.setObjectName("SearchInput")
        self.search.setPlaceholderText("Buscar matérias, módulos, blocos ou perguntas...")
        self.search.setToolTip("Digite uma busca e pressione Enter.")
        self.search.returnPressed.connect(lambda: self.search_submitted.emit(self.search.text()))
        self.search.textChanged.connect(self.search_changed.emit)
        self._suggestion_model = QStringListModel(self)
        self.completer = QCompleter(self._suggestion_model, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.activated[str].connect(self.search_suggestion_selected.emit)
        self.search.setCompleter(self.completer)
        search_layout.addWidget(self.search, 1)
        layout.addWidget(search_box, 1)

        self.subject_selector = SubjectSelector(subjects)
        self.subject_selector.currentTextChanged.connect(self.subject_changed.emit)
        layout.addWidget(self.subject_selector)

    def refresh_subjects(self, subjects: list[UISubject]) -> None:
        self.subject_selector.blockSignals(True)
        self.subject_selector.refresh(subjects)
        self.subject_selector.blockSignals(False)

    def set_search_suggestions(self, suggestions: list[str]) -> None:
        self._suggestion_model.setStringList(suggestions[:12])
