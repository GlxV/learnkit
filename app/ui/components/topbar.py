from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLineEdit

from app.ui.components.icons import LineIcon
from app.ui.components.subject_selector import SubjectSelector
from app.ui.mock_data import UISubject


class TopBar(QFrame):
    subject_changed = Signal(str)
    search_submitted = Signal(str)

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
        self.search.setPlaceholderText("Buscar materias, modulos, blocos ou perguntas...")
        self.search.setToolTip("Digite uma busca e pressione Enter.")
        self.search.returnPressed.connect(lambda: self.search_submitted.emit(self.search.text()))
        search_layout.addWidget(self.search, 1)
        layout.addWidget(search_box, 1)

        self.subject_selector = SubjectSelector(subjects)
        self.subject_selector.currentTextChanged.connect(self.subject_changed.emit)
        layout.addWidget(self.subject_selector)

    def refresh_subjects(self, subjects: list[UISubject]) -> None:
        self.subject_selector.blockSignals(True)
        self.subject_selector.refresh(subjects)
        self.subject_selector.blockSignals(False)
