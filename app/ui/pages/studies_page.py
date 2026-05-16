from __future__ import annotations

import json

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.application.query_services.study_session_query_service import StudySessionQueryService
from app.application.query_services.ui_data_provider import UIBlock, UIDataProvider, UIModule, UISubject
from app.application.use_cases.manage_study_summary import ManageStudySummaryUseCase
from app.core.storage.local_storage import LocalStorage
from app.ui.components.cards import EmptyState, ProgressLine, StatCard, StudyBlockRow, label
from app.ui.components.summary_visual import PresentationDialog, VisualSummaryWidget
from app.ui.feedback import log_action, show_toast
from app.ui.pages.base import panel, scroll_page
from app.ui.theme import COLORS


class SummaryEditDialog(QDialog):
    def __init__(self, block, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Editar resumo")
        self.resize(880, 700)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(label("Editar resumo", "Title"))
        layout.addWidget(label("Ajuste o Markdown do modo Texto e, opcionalmente, o JSON do modo Visual.", "Muted"))

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Texto", "text")
        self.mode_combo.addItem("Visual", "visual")
        self.mode_combo.setCurrentIndex(1 if block.preferred_summary_mode == "visual" else 0)
        layout.addWidget(self.mode_combo)

        layout.addWidget(label("Resumo em texto", "SectionTitle"))
        self.text_editor = QPlainTextEdit()
        self.text_editor.setPlaceholderText("Resumo em Markdown")
        self.text_editor.setPlainText(block.summary.content if block.summary else "")
        self.text_editor.setMinimumHeight(220)
        layout.addWidget(self.text_editor)

        layout.addWidget(label("Resumo visual em JSON", "SectionTitle"))
        self.visual_editor = QPlainTextEdit()
        self.visual_editor.setPlaceholderText('{"title":"...","sections":[]}')
        self.visual_editor.setPlainText(block.summary_visual or "")
        self.visual_editor.setMinimumHeight(240)
        layout.addWidget(self.visual_editor)

        self.status = label("JSON visual vazio é permitido; nesse caso o app usa o modo Texto.", "Weak")
        layout.addWidget(self.status)

        actions = QHBoxLayout()
        validate = QPushButton("Validar JSON visual")
        validate.clicked.connect(self._validate_visual)
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Salvar resumo")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(self._accept_if_valid)
        actions.addWidget(validate)
        actions.addStretch()
        actions.addWidget(cancel)
        actions.addWidget(save)
        layout.addLayout(actions)

    def values(self) -> tuple[str, str, str]:
        return (
            self.text_editor.toPlainText(),
            self.visual_editor.toPlainText(),
            str(self.mode_combo.currentData() or "text"),
        )

    def _validate_visual(self) -> bool:
        raw = self.visual_editor.toPlainText().strip()
        if not raw:
            self.status.setText("Sem JSON visual. O modo Texto continuará disponível.")
            show_toast(self, "Resumo visual vazio.", "info")
            return True
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            self.status.setText(f"JSON inválido: {exc.msg}")
            show_toast(self, f"JSON visual inválido: {exc.msg}", "warning")
            return False
        if not isinstance(parsed, dict):
            self.status.setText("JSON visual precisa ser um objeto.")
            show_toast(self, "JSON visual precisa ser um objeto.", "warning")
            return False
        self.visual_editor.setPlainText(json.dumps(parsed, ensure_ascii=False, indent=2))
        self.status.setText("JSON visual válido.")
        show_toast(self, "JSON visual válido.", "success")
        return True

    def _accept_if_valid(self) -> None:
        if self._validate_visual():
            self.accept()


class SummaryDialog(QDialog):
    def __init__(
        self,
        study_session_query_service: StudySessionQueryService,
        summary_use_case: ManageStudySummaryUseCase,
        block_id: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.study_session_query_service = study_session_query_service
        self.summary_use_case = summary_use_case
        context = self.study_session_query_service.block_context(block_id)
        self.subject, self.module, self.block = context.subject, context.module, context.block
        self.setWindowTitle(f"Resumo - {self.block.title}")
        self.resize(980, 720)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = label(self.block.title, "Title")
        subtitle = label(f"{self.subject.name} > {self.module.name}", "Muted")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)

        self.text_button = QPushButton("Texto")
        self.text_button.setCheckable(True)
        self.text_button.clicked.connect(lambda: self._set_mode("text"))
        self.visual_button = QPushButton("Visual")
        self.visual_button.setCheckable(True)
        self.visual_button.clicked.connect(lambda: self._set_mode("visual"))
        copy = QPushButton("Copiar")
        copy.clicked.connect(self._copy_current)
        edit = QPushButton("Editar")
        edit.clicked.connect(self._edit_summary)
        self.presentation = QPushButton("Modo apresentação")
        self.presentation.clicked.connect(self._open_presentation)
        self.presentation.setEnabled(bool(self.block.summary_visual.strip()))
        self.presentation.setToolTip("" if self.presentation.isEnabled() else "Disponível quando houver resumo visual.")
        for widget in [self.text_button, self.visual_button, copy, edit, self.presentation]:
            header.addWidget(widget)
        layout.addLayout(header)

        self.stack = QStackedWidget()
        self.text_viewer = QTextBrowser()
        self.text_viewer.setOpenExternalLinks(False)
        markdown = self.block.summary.content if self.block.summary else ""
        self.text_viewer.setMarkdown(markdown or "Este bloco ainda não possui resumo importado.")
        self.visual_viewer = VisualSummaryWidget(self.block.summary_visual)
        self.stack.addWidget(self.text_viewer)
        self.stack.addWidget(self.visual_viewer)
        layout.addWidget(self.stack, 1)

        close = QPushButton("Fechar")
        close.clicked.connect(self.accept)
        layout.addWidget(close)
        preferred = self.block.preferred_summary_mode if self.block.summary_visual else "text"
        self._set_mode(preferred, save=False)

    def _set_mode(self, mode: str, save: bool = True) -> None:
        normalized = "visual" if mode == "visual" and self.block.summary_visual else "text"
        self.stack.setCurrentIndex(1 if normalized == "visual" else 0)
        self.text_button.setChecked(normalized == "text")
        self.visual_button.setChecked(normalized == "visual")
        self.presentation.setVisible(normalized == "visual")
        if save:
            self.block = self.summary_use_case.set_preferred_mode(self.block.id, normalized)

    def _copy_current(self) -> None:
        if self.stack.currentWidget() is self.visual_viewer:
            text = self.block.summary_visual
        else:
            text = self.block.summary.content if self.block.summary else ""
        QApplication.clipboard().setText(text)
        show_toast(self, "Resumo copiado.", "success")

    def _open_presentation(self) -> None:
        if not self.block.summary_visual:
            show_toast(self, "Este bloco ainda não possui resumo visual.", "warning")
            return
        dialog = PresentationDialog(self.block.title, self.block.summary_visual, self)
        dialog.showMaximized()
        dialog.exec()

    def _edit_summary(self) -> None:
        dialog = SummaryEditDialog(self.block, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        summary_text, summary_visual, preferred = dialog.values()
        try:
            updated = self.summary_use_case.update_summary(
                self.block.id,
                summary_markdown=summary_text,
                summary_visual=summary_visual,
                preferred_summary_mode=preferred,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Resumo inválido", str(exc))
            return
        self.block = updated
        self._reload_views()
        show_toast(self, "Resumo salvo.", "success")
        log_action("summary_edited", block_id=self.block.id, preferred=self.block.preferred_summary_mode)

    def _reload_views(self) -> None:
        context = self.study_session_query_service.block_context(self.block.id)
        self.subject, self.module, self.block = context.subject, context.module, context.block
        markdown = self.block.summary.content if self.block.summary else ""
        self.text_viewer.setMarkdown(markdown or "Este bloco ainda não possui resumo importado.")
        self.stack.removeWidget(self.visual_viewer)
        self.visual_viewer.deleteLater()
        self.visual_viewer = VisualSummaryWidget(self.block.summary_visual)
        self.stack.addWidget(self.visual_viewer)
        self.presentation.setEnabled(bool(self.block.summary_visual.strip()))
        self.presentation.setToolTip("" if self.presentation.isEnabled() else "Disponível quando houver resumo visual.")
        preferred = self.block.preferred_summary_mode if self.block.summary_visual else "text"
        self._set_mode(preferred, save=False)


class StudiesPage(QWidget):
    def __init__(self, provider: UIDataProvider, storage: LocalStorage) -> None:
        super().__init__()
        self.provider = provider
        self.study_session_query_service = StudySessionQueryService(storage)
        self.summary_use_case = ManageStudySummaryUseCase(storage)
        self.subjects: list[UISubject] = []
        self.subject_combo: QComboBox | None = None
        self.module_combo: QComboBox | None = None
        self.selected_block_id: str | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll, _, self.layout = scroll_page()
        root.addWidget(scroll)
        self.refresh()

    def refresh(self) -> None:
        self._clear_layout(self.layout)
        self.subjects = self.provider.subjects()
        blocks = self.provider.all_blocks()

        self.layout.addWidget(label("Estudos", "Title"))
        self.layout.addWidget(label("Escolha um destino real e continue por resumo, flashcards ou perguntas.", "Muted"))

        if not blocks:
            empty = EmptyState(
                "Você ainda não tem blocos de estudo.",
                "Importe um PDF, PPTX, TXT ou Markdown para gerar um pacote completo.",
            )
            empty_layout = empty.layout()
            if empty_layout is not None:
                action = QPushButton("Importar conteúdo")
                action.setObjectName("PrimaryButton")
                action.clicked.connect(lambda: self._navigate("import"))
                empty_layout.addWidget(action)
            self.layout.addWidget(empty)
            self.layout.addStretch()
            return

        self.layout.addLayout(self._filters())
        selected_blocks = self._filtered_blocks() or blocks
        current = self._best_block(selected_blocks)
        if self.selected_block_id:
            current = next((block for block in selected_blocks if block.id == self.selected_block_id), current)
        self.layout.addWidget(self._continue_card(current))
        self.layout.addLayout(self._study_modes(current))
        self.layout.addLayout(self._content_grid(selected_blocks))

    def _filters(self) -> QHBoxLayout:
        filters = QHBoxLayout()
        self.subject_combo = QComboBox()
        self.subject_combo.addItems([subject.name for subject in self.subjects])
        self.module_combo = QComboBox()
        self.subject_combo.currentTextChanged.connect(self._refresh_modules)
        self.module_combo.currentTextChanged.connect(lambda: self.refresh())
        filters.addWidget(self.subject_combo)
        filters.addWidget(self.module_combo)
        filters.addStretch()
        self._refresh_modules(rebuild=False)
        return filters

    def _refresh_modules(self, *_args, rebuild: bool = True) -> None:
        if self.module_combo is None or self.subject_combo is None:
            return
        subject = self._selected_subject()
        current = self.module_combo.currentText()
        self.module_combo.blockSignals(True)
        self.module_combo.clear()
        if subject:
            self.module_combo.addItems([module.name for module in subject.modules])
        index = self.module_combo.findText(current)
        if index >= 0:
            self.module_combo.setCurrentIndex(index)
        self.module_combo.blockSignals(False)
        if rebuild:
            self.refresh()

    def _continue_card(self, block: UIBlock) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)
        layout.addWidget(label("Continuar de onde parou", "SectionTitle"))
        layout.addWidget(label(block.title, "HeroTitle"))
        layout.addWidget(label(f"{block.subject_name} > {block.module_name}", "Muted"))
        layout.addWidget(ProgressLine(block.progress))
        row = QHBoxLayout()
        row.addWidget(label(f"{block.progress}% concluído", "Weak"))
        row.addStretch()
        row.addWidget(label(f"{block.flashcards} cards - {block.questions} perguntas", "Weak"))
        layout.addLayout(row)
        actions = QHBoxLayout()
        continue_button = QPushButton("Continuar estudo")
        continue_button.setObjectName("PrimaryButton")
        continue_button.clicked.connect(lambda: self._record_and_open(block))
        summary_button = QPushButton("Ver resumo")
        summary_button.clicked.connect(lambda: self._show_summary(block))
        actions.addWidget(continue_button)
        actions.addWidget(summary_button)
        actions.addStretch()
        layout.addLayout(actions)
        return card

    def _study_modes(self, block: UIBlock) -> QGridLayout:
        modes = QGridLayout()
        cards = [
            ("Resumo", "Abrir", "leitura organizada", "summary", lambda: self._show_summary(block)),
            ("Flashcards", str(block.flashcards), "cards neste bloco", "flashcards", lambda: self._navigate("flashcards")),
            ("Perguntas", str(block.questions), "questões neste bloco", "questions", lambda: self._navigate("questions")),
        ]
        for index, (title, value, subtitle, icon, handler) in enumerate(cards):
            wrap = panel()
            wrap_layout = QVBoxLayout(wrap)
            wrap_layout.setContentsMargins(16, 14, 16, 14)
            wrap_layout.addWidget(StatCard(title, value, subtitle, icon))
            button = QPushButton("Abrir")
            button.setObjectName("PrimaryButton" if index == 0 else "GhostButton")
            button.clicked.connect(handler)
            wrap_layout.addWidget(button)
            modes.addWidget(wrap, 0, index)
        return modes

    def _content_grid(self, blocks: list[UIBlock]) -> QHBoxLayout:
        content = QHBoxLayout()
        left = QVBoxLayout()
        right = QVBoxLayout()
        content.addLayout(left, 2)
        content.addLayout(right, 1)

        recent = panel()
        recent_layout = QVBoxLayout(recent)
        recent_layout.setContentsMargins(18, 16, 18, 16)
        recent_layout.setSpacing(10)
        recent_layout.addWidget(label("Blocos deste estudo", "SectionTitle"))
        for block in blocks[:8]:
            row = StudyBlockRow(block)
            row.open_requested.connect(self.select_block_by_id)
            recent_layout.addWidget(row)
        left.addWidget(recent)

        stats = self.provider.global_stats()
        plan = panel()
        plan_layout = QVBoxLayout(plan)
        plan_layout.setContentsMargins(18, 16, 18, 16)
        plan_layout.addWidget(label("Planejamento", "SectionTitle"))
        plan_layout.addWidget(label(f"Flashcards revisados: {stats.flashcards_reviewed}/{stats.total_flashcards}", "Muted"))
        plan_layout.addWidget(label(f"Perguntas respondidas: {stats.questions_answered}/{stats.total_questions}", "Muted"))
        plan_layout.addWidget(label(f"Tempo registrado: {stats.study_time_seconds // 60} min", "Muted"))
        right.addWidget(plan)

        next_steps = panel()
        next_layout = QVBoxLayout(next_steps)
        next_layout.setContentsMargins(18, 16, 18, 16)
        next_layout.addWidget(label("Próximas ações", "SectionTitle"))
        next_layout.addWidget(label("Revise cards marcados como difícil e responda perguntas em branco.", "Muted"))
        import_button = QPushButton("Importar novo bloco")
        import_button.clicked.connect(lambda: self._navigate("import"))
        next_layout.addWidget(import_button)
        right.addWidget(next_steps)
        right.addStretch()
        return content

    def _filtered_blocks(self) -> list[UIBlock]:
        module = self._selected_module()
        if module:
            return module.blocks
        subject = self._selected_subject()
        if subject:
            return [block for module in subject.modules for block in module.blocks]
        return []

    def _best_block(self, blocks: list[UIBlock]) -> UIBlock:
        return sorted(blocks, key=lambda item: (item.progress, item.flashcards + item.questions), reverse=True)[0]

    def select_block_by_id(self, block_id: str) -> None:
        self.selected_block_id = block_id
        self.refresh()

    def _record_and_open(self, block: UIBlock) -> None:
        if block.id:
            self.study_session_query_service.record_access(block.id)
            log_action("block_accessed", block_id=block.id)
        self._show_summary(block)

    def _show_summary(self, block: UIBlock) -> None:
        if not block.id:
            QMessageBox.information(self, "Resumo", "Este bloco ainda nao esta salvo no storage real.")
            return
        context = self.study_session_query_service.block_context(block.id)
        show_toast(self, f"Abrindo resumo: {context.block.title}", "info")
        SummaryDialog(
            self.study_session_query_service,
            self.summary_use_case,
            context.block.id,
            self,
        ).exec()

    def _selected_subject(self) -> UISubject | None:
        if self.subject_combo is None:
            return self.subjects[0] if self.subjects else None
        return next((subject for subject in self.subjects if subject.name == self.subject_combo.currentText()), None)

    def _selected_module(self) -> UIModule | None:
        subject = self._selected_subject()
        if not subject:
            return None
        if self.module_combo is None:
            return subject.modules[0] if subject.modules else None
        return next((module for module in subject.modules if module.name == self.module_combo.currentText()), None)

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
