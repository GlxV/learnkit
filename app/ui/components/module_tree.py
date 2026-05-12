from __future__ import annotations

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from app.ui.mock_data import UISubject


class ModuleTree(QTreeWidget):
    def __init__(self, subjects: list[UISubject]) -> None:
        super().__init__()
        self.setHeaderHidden(True)
        self.setAlternatingRowColors(False)
        self.refresh(subjects)

    def refresh(self, subjects: list[UISubject]) -> None:
        self.clear()
        for subject in subjects:
            subject_item = QTreeWidgetItem([subject.name])
            self.addTopLevelItem(subject_item)
            for module in subject.modules:
                module_item = QTreeWidgetItem([module.name])
                subject_item.addChild(module_item)
                for block in module.blocks:
                    module_item.addChild(QTreeWidgetItem([block.title]))
            subject_item.setExpanded(True)
