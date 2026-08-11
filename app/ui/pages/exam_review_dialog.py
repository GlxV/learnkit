from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.application.query_services.ui_data_provider import UIDataProvider
from app.ui.components.cards import label
from app.ui.pages.base import panel


@dataclass(frozen=True, slots=True)
class ExamReviewSelection:
    block_ids: list[str]
    include_summary: bool
    include_flashcards: bool
    include_questions: bool
    include_exam_traps: bool


class ExamReviewSelectionDialog(QDialog):
    """Selects a hierarchy of study content for a virtual exam review session."""

    def __init__(self, provider: UIDataProvider, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.provider = provider
        self.setWindowTitle("Revisão para Prova")
        self.resize(760, 680)
        self._updating_tree = False
        self._block_items: dict[str, QTreeWidgetItem] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)
        layout.addWidget(label("Revisão para Prova", "Title"))
        layout.addWidget(
            label(
                "Selecione matérias, módulos ou blocos. A seleção de um nível inclui automaticamente seus blocos filhos.",
                "Muted",
            )
        )

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Conteúdo", "Blocos"])
        self.tree.setAlternatingRowColors(False)
        self.tree.itemChanged.connect(self._item_changed)
        self._populate_tree()
        layout.addWidget(self.tree, 1)

        options = panel()
        options_layout = QVBoxLayout(options)
        options_layout.setContentsMargins(16, 14, 16, 14)
        options_layout.setSpacing(8)
        options_layout.addWidget(label("O que incluir", "SectionTitle"))
        self.summary_check = QCheckBox("Resumos")
        self.summary_check.setChecked(True)
        self.flashcards_check = QCheckBox("Flashcards")
        self.flashcards_check.setChecked(True)
        self.questions_check = QCheckBox("Perguntas")
        self.questions_check.setChecked(True)
        self.exam_traps_check = QCheckBox("Pegadinhas/armadilhas de prova")
        self.exam_traps_check.setChecked(True)
        for checkbox in (
            self.summary_check,
            self.flashcards_check,
            self.questions_check,
            self.exam_traps_check,
        ):
            options_layout.addWidget(checkbox)
        layout.addWidget(options)

        self.selection_status = label("Nenhum bloco selecionado.", "Muted")
        layout.addWidget(self.selection_status)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        buttons.accepted.connect(self._accept_selection)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Iniciar revisão")
        layout.addWidget(buttons)

    def selection(self) -> ExamReviewSelection:
        return ExamReviewSelection(
            block_ids=self.selected_block_ids(),
            include_summary=self.summary_check.isChecked(),
            include_flashcards=self.flashcards_check.isChecked(),
            include_questions=self.questions_check.isChecked(),
            include_exam_traps=self.exam_traps_check.isChecked(),
        )

    def selected_block_ids(self) -> list[str]:
        return [
            block_id
            for block_id, item in self._block_items.items()
            if item.checkState(0) == Qt.CheckState.Checked
        ]

    def _populate_tree(self) -> None:
        for subject in self.provider.subjects():
            subject_item = self._node(subject.name, "subject", subject.id or subject.slug)
            subject_item.setText(1, str(sum(len(module.blocks) for module in subject.modules)))
            self.tree.addTopLevelItem(subject_item)
            for module in subject.modules:
                module_item = self._node(module.name, "module", module.id or module.slug)
                module_item.setText(1, str(len(module.blocks)))
                subject_item.addChild(module_item)
                for block in module.blocks:
                    if not block.id:
                        continue
                    block_item = self._node(block.title, "block", block.id)
                    module_item.addChild(block_item)
                    self._block_items[block.id] = block_item
            subject_item.setExpanded(True)
            for index in range(subject_item.childCount()):
                subject_item.child(index).setExpanded(True)

    def _node(self, text: str, kind: str, value: str) -> QTreeWidgetItem:
        item = QTreeWidgetItem([text, ""])
        item.setData(0, Qt.ItemDataRole.UserRole, (kind, value))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(0, Qt.CheckState.Unchecked)
        return item

    def _item_changed(self, item: QTreeWidgetItem, _column: int) -> None:
        if self._updating_tree:
            return
        self._updating_tree = True
        try:
            if item.childCount():
                state = item.checkState(0)
                self._set_descendants(item, state)
            parent = item.parent()
            while parent is not None:
                states = [parent.child(index).checkState(0) for index in range(parent.childCount())]
                if states and all(state == Qt.CheckState.Checked for state in states):
                    parent.setCheckState(0, Qt.CheckState.Checked)
                elif any(state != Qt.CheckState.Unchecked for state in states):
                    parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
                else:
                    parent.setCheckState(0, Qt.CheckState.Unchecked)
                parent = parent.parent()
        finally:
            self._updating_tree = False
        self._update_status()

    def _set_descendants(self, item: QTreeWidgetItem, state: Qt.CheckState) -> None:
        for index in range(item.childCount()):
            child = item.child(index)
            child.setCheckState(0, state)
            if child.childCount():
                self._set_descendants(child, state)

    def _update_status(self) -> None:
        count = len(self.selected_block_ids())
        self.selection_status.setText(
            f"{count} bloco(s) selecionado(s)." if count else "Nenhum bloco selecionado."
        )

    def _accept_selection(self) -> None:
        if not self.selected_block_ids():
            self.selection_status.setText("Selecione pelo menos um bloco, módulo ou matéria.")
            return
        if not any(
            checkbox.isChecked()
            for checkbox in (
                self.summary_check,
                self.flashcards_check,
                self.questions_check,
                self.exam_traps_check,
            )
        ):
            self.selection_status.setText("Selecione pelo menos um tipo de conteúdo.")
            return
        self.accept()
