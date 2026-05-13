from __future__ import annotations

from pathlib import Path
import webbrowser

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.extractors.file_extractor import FileExtractionResult, FileExtractor
from app.core.importer.ai_response_parser import AIResponseParser, ParsedAIResponse
from app.core.models.study_block import StudyBlock
from app.core.prompt.prompt_builder import PromptBuilder, PromptOptions
from app.core.services.block_service import BlockService
from app.core.services.module_service import ModuleService
from app.core.services.subject_service import SubjectService
from app.core.storage.local_storage import LocalStorage
from app.ui.components.cards import label
from app.ui.components.file_list_item import FileListItem
from app.ui.feedback import (
    flash_button_success,
    log_action,
    set_button_loading,
    show_toast,
)
from app.ui.mock_data import UISubject
from app.ui.pages.base import panel, scroll_page
from app.ui.theme import COLORS


class ExtractionWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, files: list[Path]) -> None:
        super().__init__()
        self.files = files

    def run(self) -> None:
        try:
            self.finished.emit(FileExtractor().extract_files(self.files))
        except Exception as exc:
            self.failed.emit(str(exc))


class DropArea(QLabel):
    files_dropped = Signal(object)
    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".pptx",
        ".docx",
        ".txt",
        ".md",
        ".markdown",
        ".js",
        ".ts",
        ".py",
        ".html",
        ".css",
        ".json",
        ".csv",
    }

    def __init__(self) -> None:
        super().__init__(
            "Arraste arquivos aqui ou use o botão abaixo.\n"
            "PDF, PPTX, DOCX, TXT, MD e código/texto comum são aceitos."
        )
        self.setObjectName("Muted")
        self.setAcceptDrops(True)
        self.setMinimumHeight(92)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_style(False)

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if self._event_paths(event):
            self._apply_style(True)
            event.acceptProposedAction()
            return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:  # type: ignore[override]
        self._apply_style(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # type: ignore[override]
        paths = self._event_paths(event)
        self._apply_style(False)
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()
            return
        event.ignore()

    def _event_paths(self, event) -> list[Path]:
        mime = event.mimeData()
        if not mime.hasUrls():
            return []
        paths = [Path(url.toLocalFile()) for url in mime.urls() if url.isLocalFile()]
        return [path for path in paths if path.suffix.lower() in self.SUPPORTED_EXTENSIONS]

    def _apply_style(self, active: bool) -> None:
        border = COLORS["blue"] if active else "#2B3B55"
        background = "rgba(59, 130, 246, 0.10)" if active else "rgba(11, 22, 38, 0.36)"
        self.setStyleSheet(
            f"border: 1px dashed {border}; border-radius: 14px; "
            f"padding: 18px; background: {background};"
        )


class ImportPage(QWidget):
    def __init__(self, subjects: list[UISubject], storage: LocalStorage | None = None) -> None:
        super().__init__()
        _ = subjects
        self.storage = storage or LocalStorage("data")
        self.subject_service = SubjectService(self.storage)
        self.module_service = ModuleService(self.storage)
        self.block_service = BlockService(self.storage)
        self.prompt_builder = PromptBuilder()
        self.parser = AIResponseParser()

        self.selected_files: list[Path] = []
        self.file_statuses: dict[str, tuple[str, str]] = {}
        self.extraction_result: FileExtractionResult | None = None
        self.prompt_text = ""
        self.parsed_response: ParsedAIResponse | None = None
        self.current_block: StudyBlock | None = None
        self.worker_thread: QThread | None = None
        self.worker: ExtractionWorker | None = None
        self.result_buttons: list[QPushButton] = []
        self.step_badges: dict[int, QLabel] = {}
        self.step_statuses: dict[int, QLabel] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll, _, self.layout = scroll_page()
        root.addWidget(scroll)

        self.layout.addWidget(label("Importação / IA", "Title"))
        self.layout.addWidget(
            label(
                "Extraia o conteúdo primeiro. A matéria, o módulo e o bloco são escolhidos no final.",
                "Muted",
            )
        )
        self._build_stepper()
        self._build_files()
        self._build_extraction()
        self._build_prompt()
        self._build_response()
        self._build_destination()
        self._build_result()
        self.refresh()

    def refresh(self) -> None:
        if not hasattr(self, "subject_combo"):
            return
        current_subject = self.subject_combo.currentText().strip()
        self.subject_combo.blockSignals(True)
        self.subject_combo.clear()
        self.subject_combo.addItems([subject.name for subject in self.storage.list_subjects()])
        if current_subject:
            index = self.subject_combo.findText(current_subject)
            if index >= 0:
                self.subject_combo.setCurrentIndex(index)
            else:
                self.subject_combo.setEditText(current_subject)
        self.subject_combo.blockSignals(False)
        self._refresh_modules()
        self._refresh_destination_mode()

    def _build_stepper(self) -> None:
        card = QFrame()
        card.setObjectName("StepCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        steps = [
            (1, "Arquivos"),
            (2, "Extração"),
            (3, "Prompt"),
            (4, "Resposta"),
            (5, "Salvar"),
            (6, "Resultado"),
        ]
        for number, title in steps:
            step = QFrame()
            step.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            row = QHBoxLayout(step)
            row.setContentsMargins(6, 4, 6, 4)
            row.setSpacing(9)
            badge = QLabel(str(number))
            badge.setFixedSize(30, 30)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            text_box = QVBoxLayout()
            text_box.setSpacing(0)
            title_label = label(title, "SmallTitle")
            status_label = label("Pendente", "Weak")
            text_box.addWidget(title_label)
            text_box.addWidget(status_label)
            row.addWidget(badge)
            row.addLayout(text_box, 1)
            layout.addWidget(step)
            self.step_badges[number] = badge
            self.step_statuses[number] = status_label
            self._set_step_status(number, "pending")
        self.layout.addWidget(card)

    def _build_files(self) -> None:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(label("1. Arquivos", "SectionTitle"))
        drop = DropArea()
        drop.files_dropped.connect(self._add_files)
        layout.addWidget(drop)

        actions = QHBoxLayout()
        self.choose_button = QPushButton("Selecionar arquivos")
        self.choose_button.setObjectName("PrimaryButton")
        self.choose_button.clicked.connect(self._choose_files)
        clear = QPushButton("Limpar lista")
        clear.clicked.connect(self._clear_files)
        actions.addWidget(self.choose_button)
        actions.addWidget(clear)
        actions.addStretch()
        layout.addLayout(actions)

        self.file_empty = label("Nenhum arquivo selecionado ainda.", "Muted")
        layout.addWidget(self.file_empty)
        self.file_list = QListWidget()
        self.file_list.setSpacing(8)
        self.file_list.setMinimumHeight(108)
        layout.addWidget(self.file_list)
        self.layout.addWidget(card)

    def _build_extraction(self) -> None:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(label("2. Extração", "SectionTitle"))
        header.addStretch()
        self.extract_button = QPushButton("Extrair texto")
        self.extract_button.setObjectName("PrimaryButton")
        self.extract_button.clicked.connect(self._extract_text)
        header.addWidget(self.extract_button)
        layout.addLayout(header)

        self.extract_progress = QProgressBar()
        self.extract_progress.setRange(0, 1)
        self.extract_progress.setValue(0)
        self.extract_progress.setVisible(False)
        layout.addWidget(self.extract_progress)

        self.extraction_stats = label("Nenhum texto extraido ainda.", "Muted")
        layout.addWidget(self.extraction_stats)
        self.text_preview = QPlainTextEdit()
        self.text_preview.setPlaceholderText("Preview do texto extraido")
        self.text_preview.setMinimumHeight(230)
        layout.addWidget(self.text_preview)
        self.layout.addWidget(card)

    def _build_prompt(self) -> None:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(label("3. Prompt", "SectionTitle"))
        header.addStretch()
        self.options_button = QPushButton("Opções avançadas")
        self.options_button.clicked.connect(self._toggle_options)
        self.generate_button = QPushButton("Gerar prompt")
        self.generate_button.setObjectName("PrimaryButton")
        self.generate_button.setEnabled(False)
        self.generate_button.setToolTip("Extraia o texto antes de gerar o prompt.")
        self.generate_button.clicked.connect(self._generate_prompt)
        self.copy_button = QPushButton("Copiar prompt")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self._copy_prompt)
        gemini = QPushButton("Abrir Gemini")
        gemini.clicked.connect(self._open_gemini)
        header.addWidget(self.options_button)
        header.addWidget(self.generate_button)
        header.addWidget(self.copy_button)
        header.addWidget(gemini)
        layout.addLayout(header)

        self.options_panel = QFrame()
        self.options_panel.setObjectName("Panel")
        options_layout = QHBoxLayout(self.options_panel)
        options_layout.setContentsMargins(14, 12, 14, 12)
        options_layout.setSpacing(12)
        self.flashcard_count = QSpinBox()
        self.flashcard_count.setRange(1, 50)
        self.flashcard_count.setValue(10)
        self.question_count = QSpinBox()
        self.question_count.setRange(1, 50)
        self.question_count.setValue(10)
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["fácil", "médio", "difícil"])
        self.language_combo = QComboBox()
        self.language_combo.addItems(["simples", "acadêmica", "direta para prova"])
        self.summary_mode_combo = QComboBox()
        self.summary_mode_combo.addItems(["texto e visual", "somente texto", "visual avançado"])
        options_layout.addWidget(label("Flashcards", "Weak"))
        options_layout.addWidget(self.flashcard_count)
        options_layout.addWidget(label("Perguntas", "Weak"))
        options_layout.addWidget(self.question_count)
        options_layout.addWidget(label("Dificuldade", "Weak"))
        options_layout.addWidget(self.difficulty_combo)
        options_layout.addWidget(label("Linguagem", "Weak"))
        options_layout.addWidget(self.language_combo)
        options_layout.addWidget(label("Resumo", "Weak"))
        options_layout.addWidget(self.summary_mode_combo, 1)
        self.options_panel.setVisible(False)
        layout.addWidget(self.options_panel)

        self.prompt_preview = QPlainTextEdit()
        self.prompt_preview.setPlaceholderText("Prompt pronto para copiar e usar em uma IA gratuita externa")
        self.prompt_preview.setMinimumHeight(210)
        layout.addWidget(self.prompt_preview)
        self.layout.addWidget(card)

    def _build_response(self) -> None:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(label("4. Resposta da IA", "SectionTitle"))
        header.addStretch()
        self.validate_button = QPushButton("Validar resposta")
        self.validate_button.setObjectName("PrimaryButton")
        self.validate_button.clicked.connect(self._validate_response)
        header.addWidget(self.validate_button)
        layout.addLayout(header)
        self.ai_response = QPlainTextEdit()
        self.ai_response.setPlaceholderText("Cole aqui o Markdown retornado pela IA")
        self.ai_response.setMinimumHeight(210)
        layout.addWidget(self.ai_response)
        self.response_status = label("Aguardando resposta Markdown.", "Muted")
        layout.addWidget(self.response_status)
        self.layout.addWidget(card)

    def _build_destination(self) -> None:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(label("5. Salvar no LearnKit", "SectionTitle"))
        layout.addWidget(
            label(
                "Agora escolha onde o pacote de estudo será salvo. Matérias e módulos novos são criados automaticamente.",
                "Muted",
            )
        )
        mode_row = QHBoxLayout()
        mode_row.addWidget(label("Modo de salvamento", "Weak"))
        self.save_mode_combo = QComboBox()
        self.save_mode_combo.addItem("Criar novo bloco", "create")
        self.save_mode_combo.addItem("Atualizar bloco existente", "update")
        self.save_mode_combo.currentIndexChanged.connect(self._refresh_destination_mode)
        mode_row.addWidget(self.save_mode_combo)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        row = QHBoxLayout()
        self.subject_combo = QComboBox()
        self.subject_combo.setEditable(True)
        self.subject_combo.setPlaceholderText("Materia")
        self.subject_combo.currentTextChanged.connect(self._refresh_modules)
        self.module_combo = QComboBox()
        self.module_combo.setEditable(True)
        self.module_combo.setPlaceholderText("Modulo")
        self.module_combo.currentTextChanged.connect(self._refresh_existing_blocks)
        self.block_title = QLineEdit()
        self.block_title.setPlaceholderText("Nome do bloco de estudo")
        row.addWidget(self.subject_combo)
        row.addWidget(self.module_combo)
        row.addWidget(self.block_title, 1)
        layout.addLayout(row)
        self.existing_block_label = label("Bloco existente", "Weak")
        self.existing_block_combo = QComboBox()
        self.existing_block_combo.setToolTip("Escolha o bloco que recebera o novo pacote importado.")
        layout.addWidget(self.existing_block_label)
        layout.addWidget(self.existing_block_combo)
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Descricao opcional")
        layout.addWidget(self.description_input)
        save_row = QHBoxLayout()
        self.save_button = QPushButton("Salvar bloco de estudo")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.setEnabled(False)
        self.save_button.setToolTip("Valide a resposta da IA antes de salvar.")
        self.save_button.clicked.connect(self._save_block)
        save_row.addStretch()
        save_row.addWidget(self.save_button)
        layout.addLayout(save_row)
        self.layout.addWidget(card)

    def _build_result(self) -> None:
        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(label("6. Próximo passo", "SectionTitle"))
        self.status = label("Aguardando criação do bloco.", "Muted")
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        for text, target in [
            ("Abrir resumo", "studies"),
            ("Estudar flashcards", "flashcards"),
            ("Responder perguntas", "questions"),
            ("Ir para módulo", "subjects"),
        ]:
            button = QPushButton(text)
            button.setEnabled(False)
            button.setToolTip("Disponivel depois de salvar o bloco.")
            button.clicked.connect(lambda checked=False, key=target: self._navigate(key))
            self.result_buttons.append(button)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        self.layout.addWidget(card)

    def _set_step_status(self, step: int, status: str) -> None:
        badge = self.step_badges.get(step)
        label_widget = self.step_statuses.get(step)
        if badge is None or label_widget is None:
            return
        colors = {
            "pending": COLORS["weak"],
            "active": COLORS["blue"],
            "done": COLORS["green"],
            "warning": COLORS["amber"],
            "error": COLORS["red"],
        }
        texts = {
            "pending": "Pendente",
            "active": "Em andamento",
            "done": "Concluida",
            "warning": "Aviso",
            "error": "Erro",
        }
        color = colors.get(status, COLORS["weak"])
        badge.setStyleSheet(
            f"background: rgba(59, 130, 246, 0.14); border: 1px solid {color}; "
            f"border-radius: 15px; color: {color}; font-weight: 800;"
        )
        label_widget.setText(texts.get(status, status))
        label_widget.setStyleSheet(f"color: {color}; font-size: 12px;")

    def _refresh_modules(self, *_args: object) -> None:
        if not hasattr(self, "module_combo"):
            return
        selected = self.subject_combo.currentText().strip()
        current_module = self.module_combo.currentText().strip()
        self.module_combo.blockSignals(True)
        self.module_combo.clear()
        if selected:
            try:
                self.module_combo.addItems(
                    [module.name for module in self.storage.list_modules(selected)]
                )
            except ValueError:
                pass
        if self.module_combo.count() == 0:
            self.module_combo.addItems(["Geral", "Prova 1", "Revisão Final"])
        if current_module:
            index = self.module_combo.findText(current_module)
            if index >= 0:
                self.module_combo.setCurrentIndex(index)
            else:
                self.module_combo.setEditText(current_module)
        self.module_combo.blockSignals(False)
        self._refresh_existing_blocks()

    def _refresh_existing_blocks(self, *_args: object) -> None:
        if not hasattr(self, "existing_block_combo"):
            return
        current = self.existing_block_combo.currentData()
        subject_ref = self.subject_combo.currentText().strip()
        module_ref = self.module_combo.currentText().strip()
        self.existing_block_combo.blockSignals(True)
        self.existing_block_combo.clear()
        blocks = []
        if subject_ref and module_ref:
            try:
                blocks = self.storage.list_blocks(subject_ref, module_ref)
            except ValueError:
                blocks = []
        for block in blocks:
            self.existing_block_combo.addItem(block.title, block.id)
        if current:
            for index in range(self.existing_block_combo.count()):
                if self.existing_block_combo.itemData(index) == current:
                    self.existing_block_combo.setCurrentIndex(index)
                    break
        if self.existing_block_combo.count() == 0:
            self.existing_block_combo.addItem("Nenhum bloco existente neste modulo", None)
        self.existing_block_combo.blockSignals(False)
        self._refresh_destination_mode()

    def _refresh_destination_mode(self, *_args: object) -> None:
        if not hasattr(self, "save_mode_combo"):
            return
        update_mode = self._is_update_mode()
        has_existing_block = bool(self.existing_block_combo.currentData()) if hasattr(self, "existing_block_combo") else False
        self.block_title.setEnabled(not update_mode)
        self.block_title.setToolTip(
            "No modo de atualizacao, o titulo vem do bloco existente."
            if update_mode
            else ""
        )
        self.existing_block_label.setVisible(update_mode)
        self.existing_block_combo.setVisible(update_mode)
        self.existing_block_combo.setEnabled(update_mode and has_existing_block)
        self.save_button.setText("Atualizar bloco de estudo" if update_mode else "Salvar bloco de estudo")

    def _is_update_mode(self) -> bool:
        if not hasattr(self, "save_mode_combo"):
            return False
        return self.save_mode_combo.currentData() == "update"

    def _selected_existing_block_title(self) -> str:
        if not hasattr(self, "existing_block_combo"):
            return ""
        data = self.existing_block_combo.currentData()
        return self.existing_block_combo.currentText().strip() if data else ""

    def _choose_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar arquivos",
            "",
            "Materiais (*.pdf *.pptx *.docx *.txt *.md *.markdown *.js *.ts *.py *.html *.css *.json *.csv)",
        )
        if not files:
            return
        self._add_files([Path(file) for file in files])

    def _add_files(self, files: list[Path]) -> None:
        known = {str(path.resolve()) for path in self.selected_files}
        added = 0
        for path in files:
            if str(path.resolve()) not in known:
                self.selected_files.append(path)
                self.file_statuses[str(path)] = ("aguardando", "")
                known.add(str(path.resolve()))
                added += 1
        if added == 0:
            show_toast(self, "Nenhum arquivo novo foi adicionado.", "info")
            return
        self._reset_outputs_after_file_change()
        self._render_file_list()
        self._set_step_status(1, "done")
        show_toast(self, f"{added} arquivo(s) adicionado(s).", "info")
        log_action("files_added", count=added)

    def _clear_files(self) -> None:
        self.selected_files = []
        self.file_statuses = {}
        self.extraction_result = None
        self.prompt_text = ""
        self.parsed_response = None
        self.current_block = None
        self.text_preview.clear()
        self.prompt_preview.clear()
        self.ai_response.clear()
        self.extraction_stats.setText("Nenhum texto extraido ainda.")
        self.response_status.setText("Aguardando resposta Markdown.")
        self.status.setText("Aguardando criação do bloco.")
        self.generate_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)
        for button in self.result_buttons:
            button.setEnabled(False)
            button.setToolTip("Disponivel depois de salvar o bloco.")
        self._render_file_list()
        self._set_step_status(1, "pending")
        self._set_step_status(2, "pending")
        self._set_step_status(3, "pending")
        self._set_step_status(4, "pending")
        self._set_step_status(5, "pending")
        self._set_step_status(6, "pending")
        show_toast(self, "Lista de arquivos limpa.", "info")

    def _remove_file(self, path: Path) -> None:
        self.selected_files = [item for item in self.selected_files if item != path]
        self.file_statuses.pop(str(path), None)
        self._reset_outputs_after_file_change()
        self._render_file_list()
        self._set_step_status(1, "done" if self.selected_files else "pending")
        show_toast(self, f"Arquivo removido: {path.name}", "info")
        log_action("file_removed", file=path.name)

    def _reset_outputs_after_file_change(self) -> None:
        self.extraction_result = None
        self.prompt_text = ""
        self.parsed_response = None
        self.current_block = None
        self.text_preview.clear()
        self.prompt_preview.clear()
        self.ai_response.clear()
        self.extraction_stats.setText("Nenhum texto extraido ainda.")
        self.response_status.setText("Aguardando resposta Markdown.")
        self.status.setText("Aguardando criação do bloco.")
        self.generate_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)
        for button in self.result_buttons:
            button.setEnabled(False)
            button.setToolTip("Disponivel depois de salvar o bloco.")
        for step in (2, 3, 4, 5, 6):
            self._set_step_status(step, "pending")

    def _render_file_list(self) -> None:
        self.file_list.clear()
        has_files = bool(self.selected_files)
        self.file_list.setVisible(has_files)
        self.file_empty.setVisible(not has_files)
        for file in self.selected_files:
            status, detail = self.file_statuses.get(str(file), ("aguardando", ""))
            item = QListWidgetItem()
            widget = FileListItem(file, status, detail)
            widget.remove_requested.connect(self._remove_file)
            item.setSizeHint(widget.sizeHint())
            self.file_list.addItem(item)
            self.file_list.setItemWidget(item, widget)

    def _extract_text(self) -> None:
        if not self.selected_files:
            show_toast(self, "Selecione pelo menos um arquivo.", "warning")
            self._set_step_status(1, "warning")
            return
        self._set_step_status(2, "active")
        for file in self.selected_files:
            self.file_statuses[str(file)] = ("extraindo", "")
        self._render_file_list()
        set_button_loading(self.extract_button, True, "Extraindo...")
        self.extract_progress.setRange(0, 0)
        self.extract_progress.setVisible(True)
        self.worker_thread = QThread(self)
        self.worker = ExtractionWorker(self.selected_files)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._extraction_finished)
        self.worker.failed.connect(self._extraction_failed)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.failed.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()
        show_toast(self, "Extração iniciada.", "info")
        log_action("extraction_started", file_count=len(self.selected_files))

    def _extraction_finished(self, result: FileExtractionResult) -> None:
        self.extraction_result = result
        self.text_preview.setPlainText(result.combined_content.text)
        warnings = [warning for item in result.files for warning in item.extraction_warnings]
        failures = [item for item in result.files if item.error_message]
        pages = sum(item.page_count or 0 for item in result.files)
        slides = sum(item.slide_count or 0 for item in result.files)
        for item in result.files:
            status = "erro" if item.error_message else ("aviso" if item.extraction_warnings else "extraido")
            details = item.error_message or (item.extraction_warnings[0] if item.extraction_warnings else "")
            original = Path(item.imported_file.original_path)
            key = next(
                (
                    str(file)
                    for file in self.selected_files
                    if file == original or file.resolve() == original.resolve()
                ),
                item.imported_file.original_path,
            )
            self.file_statuses[key] = (status, details)
        self._render_file_list()
        self.extraction_stats.setText(
            f"{result.combined_content.character_count} caracteres - "
            f"{result.combined_content.word_count} palavras - "
            f"{len(result.files)} arquivos - {pages} paginas - {slides} slides - "
            f"{len(warnings)} avisos - {len(failures)} falhas"
        )
        self.generate_button.setEnabled(bool(result.combined_content.text.strip()))
        self.generate_button.setToolTip("")
        self._reset_extraction_button()
        if failures and not result.combined_content.text.strip():
            self._set_step_status(2, "error")
            show_toast(self, "Nao foi possivel extrair texto dos arquivos.", "error")
        elif warnings or failures:
            self._set_step_status(2, "warning")
            show_toast(self, "Texto extraido com avisos. Confira o preview.", "warning")
        else:
            self._set_step_status(2, "done")
            show_toast(self, "Texto extraido com sucesso.", "success")
        log_action(
            "extraction_finished",
            files=len(result.files),
            chars=result.combined_content.character_count,
            warnings=len(warnings),
            failures=len(failures),
        )

    def _extraction_failed(self, message: str) -> None:
        self._reset_extraction_button()
        self._set_step_status(2, "error")
        show_toast(self, f"Erro na extracao: {message}", "error")
        log_action("extraction_failed", error=message)

    def _reset_extraction_button(self) -> None:
        self.extract_progress.setVisible(False)
        self.extract_progress.setRange(0, 1)
        set_button_loading(self.extract_button, False)

    def _toggle_options(self) -> None:
        visible = not self.options_panel.isVisible()
        self.options_panel.setVisible(visible)
        self.options_button.setText("Ocultar opções" if visible else "Opções avançadas")

    def _generate_prompt(self) -> None:
        if not self.extraction_result or not self.extraction_result.combined_content.text.strip():
            show_toast(self, "Extraia o texto antes de gerar o prompt.", "warning")
            self._set_step_status(3, "warning")
            return
        options = PromptOptions(
            flashcard_count=int(self.flashcard_count.value()),
            question_count=int(self.question_count.value()),
            difficulty=self.difficulty_combo.currentText(),
            language_style=self.language_combo.currentText(),
            summary_mode=self.summary_mode_combo.currentText(),
        )
        subject = self.subject_combo.currentText().strip() or "Materia a definir"
        module = self.module_combo.currentText().strip() or "Modulo a definir"
        block = (
            self._selected_existing_block_title()
            if self._is_update_mode()
            else self.block_title.text().strip()
        ) or "Bloco de estudo a definir"
        self.prompt_text = self.prompt_builder.build(
            subject_name=subject,
            module_name=module,
            block_title=block,
            extracted_content=self.extraction_result.combined_content,
            options=options,
        )
        self.prompt_preview.setPlainText(self.prompt_text)
        self.copy_button.setEnabled(True)
        self._set_step_status(3, "done")
        flash_button_success(self.generate_button, "Gerado!")
        show_toast(self, "Prompt gerado.", "success")
        log_action("prompt_generated", chars=len(self.prompt_text))

    def _copy_prompt(self) -> None:
        prompt = self.prompt_preview.toPlainText()
        if not prompt.strip():
            show_toast(self, "Gere um prompt antes de copiar.", "warning")
            return
        QApplication.clipboard().setText(prompt)
        flash_button_success(self.copy_button, "Copiado!")
        show_toast(self, "Prompt copiado para a area de transferencia.", "success")
        log_action("prompt_copied", chars=len(prompt))

    def _open_gemini(self) -> None:
        webbrowser.open("https://gemini.google.com/")
        show_toast(self, "Gemini aberto no navegador.", "info")
        log_action("external_ai_opened", url="https://gemini.google.com/")

    def _validate_response(self) -> None:
        raw = self.ai_response.toPlainText().strip()
        if not raw:
            self._set_step_status(4, "warning")
            show_toast(self, "Cole a resposta da IA primeiro.", "warning")
            return
        parsed = self.parser.parse(raw)
        has_summary = bool(parsed.summary.content.strip())
        has_visual = bool(parsed.summary_visual.strip())
        has_content = has_summary or has_visual or bool(parsed.flashcards) or bool(parsed.questions)
        if not has_content:
            self.parsed_response = None
            self.save_button.setEnabled(False)
            self._set_step_status(4, "error")
            self.response_status.setText("Não foi possível identificar conteúdo válido na resposta.")
            show_toast(self, "Resposta sem resumo, flashcards ou perguntas reconheciveis.", "error")
            log_action("ai_response_validation_failed", warnings=len(parsed.warnings))
            return

        self.parsed_response = parsed
        self.response_status.setText(
            f"Resumo texto: {'sim' if has_summary else 'nao'} - "
            f"Resumo visual: {'sim' if has_visual else 'nao'} - "
            f"{len(parsed.flashcards)} flashcards - {len(parsed.questions)} perguntas - "
            f"{len(parsed.warnings)} avisos"
        )
        self.save_button.setEnabled(True)
        self.save_button.setToolTip("")
        self._set_step_status(4, "warning" if parsed.warnings else "done")
        show_toast(self, "Resposta validada. Escolha o destino e salve.", "success")
        log_action(
            "ai_response_validated",
            flashcards=len(parsed.flashcards),
            questions=len(parsed.questions),
            warnings=len(parsed.warnings),
        )

    def _save_block(self) -> None:
        if not self.extraction_result or not self.extraction_result.combined_content.text.strip():
            show_toast(self, "Extraia o texto antes de salvar.", "warning")
            return
        if not self.prompt_preview.toPlainText().strip():
            show_toast(self, "Gere o prompt antes de salvar.", "warning")
            return
        if self.parsed_response is None:
            self._validate_response()
            if self.parsed_response is None:
                return

        subject_name = self.subject_combo.currentText().strip()
        module_name = self.module_combo.currentText().strip()
        title = self.block_title.text().strip()
        description = self.description_input.text().strip() or None
        update_mode = self._is_update_mode()
        existing_block_id = (
            self.existing_block_combo.currentData()
            if hasattr(self, "existing_block_combo")
            else None
        )
        if not subject_name or not module_name or (not update_mode and not title):
            self._set_step_status(5, "warning")
            show_toast(self, "Escolha ou crie uma matéria, um módulo e informe o nome do bloco.", "warning")
            return
        if update_mode and not existing_block_id:
            self._set_step_status(5, "warning")
            show_toast(self, "Selecione um bloco existente para atualizar.", "warning")
            return

        try:
            set_button_loading(self.save_button, True, "Salvando...")
            try:
                subject = self.storage.get_subject(subject_name)
            except ValueError:
                if update_mode:
                    self._set_step_status(5, "warning")
                    show_toast(self, "Para atualizar, escolha uma materia existente.", "warning")
                    set_button_loading(self.save_button, False)
                    return
                subject = self.subject_service.create_subject(subject_name)
                log_action("subject_created_from_import", subject=subject.name)
            try:
                _, module = self.storage.get_module(subject.slug, module_name)
            except ValueError:
                if update_mode:
                    self._set_step_status(5, "warning")
                    show_toast(self, "Para atualizar, escolha um modulo existente.", "warning")
                    set_button_loading(self.save_button, False)
                    return
                module = self.module_service.create_module(subject.slug, module_name)
                log_action("module_created_from_import", subject=subject.name, module=module.name)

            if update_mode:
                block = self.block_service.update_imported_package(
                    block_id=str(existing_block_id),
                    extraction=self.extraction_result,
                    generated_prompt=self.prompt_preview.toPlainText(),
                    response_text=self.ai_response.toPlainText(),
                    parsed_response=self.parsed_response,
                    description=description,
                )
                subject, module, block = self.storage.get_block_by_id(block.id)
                action_text = "atualizado"
                toast_text = "Bloco de estudo atualizado com sucesso."
                log_name = "import_package_updated"
            else:
                block = self.block_service.save_imported_package(
                    subject_ref=subject.slug,
                    module_ref=module.slug,
                    title=title,
                    extraction=self.extraction_result,
                    generated_prompt=self.prompt_preview.toPlainText(),
                    response_text=self.ai_response.toPlainText(),
                    parsed_response=self.parsed_response,
                    description=description,
                )
                action_text = "criado"
                toast_text = "Bloco de estudo salvo com sucesso."
                log_name = "import_package_saved"
            self.current_block = block
            self._set_step_status(5, "done")
            self._set_step_status(6, "done")
            for button in self.result_buttons:
                button.setEnabled(True)
                button.setToolTip("")
            self.status.setText(
                f"Bloco {action_text}: {subject.name} > {module.name} > {block.title}. "
                f"{len(block.flashcards)} flashcards e {len(block.questions)} perguntas."
            )
            flash_button_success(self.save_button, "Salvo!")
            show_toast(self, toast_text, "success")
            log_action(
                log_name,
                block_id=block.id,
                subject=subject.name,
                module=module.name,
                flashcards=len(block.flashcards),
                questions=len(block.questions),
            )
            self.refresh()
        except Exception as exc:
            set_button_loading(self.save_button, False)
            self._set_step_status(5, "error")
            show_toast(self, f"Erro ao salvar bloco: {exc}", "error")
            log_action("import_package_save_failed", error=str(exc))

    def _navigate(self, key: str) -> None:
        window = self.window()
        if self.current_block and key == "subjects" and hasattr(window, "open_subject"):
            subject, module, _ = self.storage.get_block_by_id(self.current_block.id)
            window.open_subject(subject.name, module.name)
        elif self.current_block and hasattr(window, "open_block"):
            window.open_block(self.current_block.id, key)
        elif hasattr(window, "navigate"):
            window.navigate(key)
