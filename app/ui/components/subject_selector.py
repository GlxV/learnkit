from __future__ import annotations

from PySide6.QtWidgets import QComboBox

from app.ui.mock_data import UISubject


class SubjectSelector(QComboBox):
    ALL_SUBJECTS = "Todas as materias"

    def __init__(self, subjects: list[UISubject]) -> None:
        super().__init__()
        self.setMinimumWidth(180)
        self.setToolTip("Filtra paginas que suportam filtro por materia.")
        self.refresh(subjects)

    def refresh(self, subjects: list[UISubject]) -> None:
        current = self.currentText()
        self.clear()
        self.addItem(self.ALL_SUBJECTS)
        for subject in subjects:
            self.addItem(subject.name)
        if current:
            index = self.findText(current)
            if index >= 0:
                self.setCurrentIndex(index)
