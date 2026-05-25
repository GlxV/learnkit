from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
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
from app.application.query_services.review_cycle_query_service import ReviewCycleQueryService
from app.application.query_services.ui_data_provider import UIBlock, UIDataProvider, UIModule, UISubject
from app.application.use_cases.manage_study_summary import ManageStudySummaryUseCase
from app.application.use_cases.manage_review_cycle import ManageReviewCycleUseCase
from app.core.storage.local_storage import LocalStorage
from app.ui.components.cards import EmptyState, ProgressLine, StatCard, StudyBlockRow, label
from app.ui.components.summary_visual import PresentationDialog, VisualSummaryWidget
from app.ui.feedback import log_action, show_toast
from app.ui.pages.base import panel, scroll_page
from app.ui.pages.combined_review_dialog import CombinedReviewSessionDialog
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
        self.setObjectName("SummaryDialog")
        self.setStyleSheet(
            f"""
            QDialog#SummaryDialog {{
                background: {COLORS['background']};
            }}
            QStackedWidget {{
                background: {COLORS['background']};
                border: 0;
            }}
            QTextBrowser#SummaryTextViewer {{
                background: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 14px;
                padding: 16px;
                color: {COLORS['text']};
            }}
            """
        )
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
        self.text_viewer.setObjectName("SummaryTextViewer")
        self.text_viewer.setFrameShape(QFrame.Shape.NoFrame)
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
    def __init__(
        self,
        provider: UIDataProvider,
        storage: LocalStorage,
        settings_provider: Callable[[], Mapping[str, object]] | None = None,
    ) -> None:
        super().__init__()
        self.provider = provider
        self.storage = storage
        self.settings_provider = settings_provider or (lambda: {})
        self.study_session_query_service = StudySessionQueryService(storage, self.settings_provider)
        self.summary_use_case = ManageStudySummaryUseCase(storage)
        self.review_cycle_use_case = ManageReviewCycleUseCase(storage)
        self.review_cycle_query_service = ReviewCycleQueryService(storage)
        self.subjects: list[UISubject] = []
        self.subject_combo: QComboBox | None = None
        self.module_combo: QComboBox | None = None
        self.selected_block_id: str | None = None
        self.selected_review_block_ids: set[str] = set()
        self.selected_subject_name: str | None = None
        self.selected_module_name: str | None = None
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
        selected_blocks = self._filtered_blocks()
        if not selected_blocks:
            self.selected_review_block_ids.clear()
            self.layout.addWidget(
                EmptyState(
                    "Nenhum bloco neste módulo.",
                    "Escolha outro módulo ou importe um novo bloco para estudar.",
                )
            )
            self.layout.addStretch()
            return
        visible_ids = {block.id for block in selected_blocks if block.id}
        self.selected_review_block_ids.intersection_update(visible_ids)
        current = self._best_block(selected_blocks)
        if self.selected_block_id:
            current = next((block for block in selected_blocks if block.id == self.selected_block_id), current)
        self.layout.addWidget(self._continue_card(current))
        self.layout.addWidget(self._review_cycle_panel(current))
        self.layout.addLayout(self._study_modes(current))
        self.layout.addLayout(self._content_grid(selected_blocks))

    def _filters(self) -> QHBoxLayout:
        filters = QHBoxLayout()
        self.subject_combo = QComboBox()
        subject_names = [subject.name for subject in self.subjects]
        self.subject_combo.addItems(subject_names)
        if self.selected_subject_name not in subject_names:
            self.selected_subject_name = subject_names[0] if subject_names else None
        if self.selected_subject_name:
            self.subject_combo.setCurrentText(self.selected_subject_name)
        self.module_combo = QComboBox()
        subject = self._selected_subject()
        module_names = [module.name for module in subject.modules] if subject else []
        self.module_combo.addItems(module_names)
        if self.selected_module_name not in module_names:
            self.selected_module_name = module_names[0] if module_names else None
        if self.selected_module_name:
            self.module_combo.setCurrentText(self.selected_module_name)
        self.subject_combo.currentTextChanged.connect(self._select_subject_scope)
        self.module_combo.currentTextChanged.connect(self._select_module_scope)
        filters.addWidget(self.subject_combo)
        filters.addWidget(self.module_combo)
        filters.addStretch()
        return filters

    def _select_subject_scope(self, subject_name: str) -> None:
        if subject_name == self.selected_subject_name:
            return
        self.selected_subject_name = subject_name
        self.selected_module_name = None
        self.selected_block_id = None
        self.selected_review_block_ids.clear()
        self.refresh()

    def _select_module_scope(self, module_name: str) -> None:
        if module_name == self.selected_module_name:
            return
        self.selected_module_name = module_name
        self.selected_block_id = None
        self.selected_review_block_ids.clear()
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

    def _review_cycle_panel(self, block: UIBlock) -> QWidget:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        layout.addWidget(label("Ciclo de Revisão", "SectionTitle"))
        if not block.id:
            layout.addWidget(label("Salve este bloco para ativar um ciclo.", "Muted"))
            return card
        cycle = self.review_cycle_query_service.block_cycle(block.id)
        if cycle.total == 0:
            layout.addWidget(
                label(
                    "Nenhuma revisão agendada. Você pode ativar um ciclo somente para este bloco.",
                    "Muted",
                )
            )
            activate = QPushButton("Ativar Ciclo de Revisão")
            activate.setObjectName("PrimaryButton")
            activate.clicked.connect(lambda: self._activate_review_cycle(block.id or ""))
            layout.addWidget(activate)
            return card
        done = cycle.done + cycle.skipped
        layout.addWidget(label(f"{done} de {cycle.total} revisões encerradas.", "Muted"))
        if cycle.next_pending is not None:
            layout.addWidget(
                label(
                    f"Próxima revisão: {self._format_review_time(cycle.next_pending.scheduled_at)}",
                    "SmallTitle",
                )
            )
        else:
            layout.addWidget(label("Ciclo concluído.", "SmallTitle"))
        open_queue = QPushButton("Abrir fila de revisões")
        open_queue.setObjectName("PrimaryButton")
        open_queue.clicked.connect(lambda: self._navigate("reviews"))
        layout.addWidget(open_queue)
        return card

    def _activate_review_cycle(self, block_id: str) -> None:
        try:
            result = self.review_cycle_use_case.activate_cycle(
                block_id,
                settings=self.settings_provider(),
                automatic=False,
            )
        except ValueError as exc:
            show_toast(self, str(exc), "warning")
            return
        if result.created:
            show_toast(self, "Ciclo de Revisão ativado para este bloco.", "success")
            log_action("review_cycle_activated_manually", block_id=block_id)
        else:
            show_toast(self, "Este bloco já possui um Ciclo de Revisão.", "info")
        self.refresh()

    def _format_review_time(self, value: str) -> str:
        try:
            return datetime.fromisoformat(value).astimezone().strftime("%d/%m/%Y às %H:%M")
        except ValueError:
            return value

    def _combined_review_bar(self) -> QWidget:
        count = len(self.selected_review_block_ids)
        bar = QFrame()
        bar.setObjectName("CombinedSelectionBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        layout.addWidget(label(f"{count} blocos selecionados para revisão combinada", "SmallTitle"))
        layout.addStretch()
        clear = QPushButton("Limpar seleção")
        clear.setObjectName("GhostButton")
        clear.clicked.connect(self._clear_review_selection)
        review = QPushButton(f"Revisar selecionados ({count})")
        review.setObjectName("PrimaryButton")
        review.setEnabled(count >= 2)
        review.setToolTip("" if count >= 2 else "Selecione pelo menos dois blocos.")
        review.clicked.connect(self._open_combined_review)
        layout.addWidget(clear)
        layout.addWidget(review)
        return bar

    def _toggle_review_selection(self, block_id: str, selected: bool) -> None:
        if selected:
            self.selected_review_block_ids.add(block_id)
        else:
            self.selected_review_block_ids.discard(block_id)
        self.refresh()

    def _clear_review_selection(self) -> None:
        self.selected_review_block_ids.clear()
        self.refresh()

    def _open_combined_review(self) -> None:
        if len(self.selected_review_block_ids) < 2:
            return
        block_ids = [
            block.id
            for block in self._filtered_blocks()
            if block.id and block.id in self.selected_review_block_ids
        ]
        dialog = CombinedReviewSessionDialog(
            self.storage,
            block_ids,
            settings_provider=self.settings_provider,
            parent=self,
        )
        dialog.exec()
        self.refresh()

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
        if self.selected_review_block_ids:
            recent_layout.addWidget(self._combined_review_bar())
        for block in blocks:
            row = StudyBlockRow(
                block,
                selectable=True,
                selected=bool(block.id and block.id in self.selected_review_block_ids),
            )
            row.open_requested.connect(self.select_block_by_id)
            row.selection_changed.connect(self._toggle_review_selection)
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

    def hideEvent(self, event) -> None:  # type: ignore[override]
        self.selected_review_block_ids.clear()
        super().hideEvent(event)

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
