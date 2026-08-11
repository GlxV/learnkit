from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
import webbrowser

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QComboBox,
    QFrame,
    QGridLayout,
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
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.application.dto.study_package import ImportDestinationDTO, StudyPackageDTO, StudyPackageImportDTO
from app.application.query_services.study_session_query_service import StudySessionQueryService
from app.application.query_services.ui_data_provider import UISubject
from app.application.use_cases.generate_prompt import GeneratePromptUseCase
from app.application.use_cases.import_study_package import ImportStudyPackageUseCase
from app.application.use_cases.parse_ai_response import ParseAIResponseUseCase
from app.core.extractors.file_extractor import FileExtractionResult, FileExtractor
from app.core.models.study_block import StudyBlock
from app.core.prompt.prompt_builder import PromptOptions
from app.core.storage.local_storage import LocalStorage
from app.ui.components.cards import label
from app.ui.components.file_list_item import FileListItem
from app.ui.feedback import (
    flash_button_success,
    log_action,
    set_button_loading,
    show_toast,
)
from app.ui.pages.base import panel, scroll_page
from app.ui.theme import COLORS


AI_PROVIDERS = {
    "Gemini": "https://gemini.google.com/",
    "ChatGPT": "https://chatgpt.com/",
    "Claude": "https://claude.ai/",
}

VISUAL_STYLE_OPTIONS = [
    ("Auto", "auto"),
    ("Prova", "prova"),
    ("Lab", "lab"),
    ("Neon", "neon"),
    ("Retro", "retro"),
    ("Minimalista", "minimalista"),
]


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
        border = COLORS["accent"] if active else COLORS["border"]
        background = COLORS["accent_dark"] if active else COLORS["card"]
        self.setStyleSheet(
            f"border: 1px dashed {border}; border-radius: 14px; "
            f"padding: 18px; background: {background};"
        )


class ImportPage(QWidget):
    def __init__(
        self,
        subjects: list[UISubject],
        storage: LocalStorage | None = None,
        settings_provider: Callable[[], Mapping[str, object]] | None = None,
    ) -> None:
        super().__init__()
        _ = subjects
        self.storage = storage or LocalStorage("data")
        self.generate_prompt_use_case = GeneratePromptUseCase()
        self.parse_ai_response_use_case = ParseAIResponseUseCase()
        self.import_package_use_case = ImportStudyPackageUseCase(self.storage, settings_provider)
        self.study_session_query_service = StudySessionQueryService(self.storage)

        self.selected_files: list[Path] = []
        self.file_statuses: dict[str, tuple[str, str]] = {}
        self.extraction_result: FileExtractionResult | None = None
        self.prompt_text = ""
        self.parsed_response: StudyPackageDTO | None = None
        self.current_block: StudyBlock | None = None
        self.worker_thread: QThread | None = None
        self.worker: ExtractionWorker | None = None
        self.result_buttons: list[QPushButton] = []
        self.step_badges: dict[int, QLabel] = {}
        self.step_statuses: dict[int, QLabel] = {}
        self.step_states: dict[int, str] = {}
        self.prepare_after_extraction = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll, _, self.layout = scroll_page()
        root.addWidget(scroll)

        self.layout.addWidget(label("Importacao guiada", "Title"))
        self.layout.addWidget(
            label(
                "Escolha o destino, prepare o pacote para a IA e salve o bloco sem precisar entender o fluxo tecnico.",
                "Muted",
            )
        )
        self._build_stepper()
        self._build_context_card()
        self.wizard_stack = QStackedWidget()
        self.layout.addWidget(self.wizard_stack)
        self._build_destination()
        self._build_files()
        self._build_prepare()
        self._build_response()
        self._build_result()
        self._show_wizard_step(0)
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
        self._update_context_card()

    def _build_context_card(self) -> None:
        self.context_card = panel()
        layout = QVBoxLayout(self.context_card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        header = QHBoxLayout()
        header.addWidget(label("Contexto do pacote", "SectionTitle"))
        header.addStretch()
        self.advanced_import_button = QPushButton("Importacao avancada")
        self.advanced_import_button.clicked.connect(self._toggle_advanced_import)
        header.addWidget(self.advanced_import_button)
        layout.addLayout(header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)
        self.context_action = self._context_value("Acao", "Criar bloco novo")
        self.context_files = self._context_value("Arquivos", "Nenhum arquivo escolhido")
        self.context_destination = self._context_value("Destino", "Defina materia, modulo e bloco")
        self.context_next = self._context_value("Proximo passo", "Escolher destino")
        for index, widget in enumerate(
            [
                self.context_action,
                self.context_destination,
                self.context_files,
                self.context_next,
            ]
        ):
            grid.addWidget(widget, index // 2, index % 2)
        layout.addLayout(grid)
        self.layout.addWidget(self.context_card)

    def _context_value(self, title: str, value: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Panel")
        frame.setStyleSheet(
            f"QFrame#Panel {{ background: {COLORS['card_alt']}; border: 1px solid {COLORS['border']}; border-radius: 12px; }}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)
        layout.addWidget(label(title, "Weak"))
        value_label = label(value, "SmallTitle")
        value_label.setProperty("context_value", True)
        layout.addWidget(value_label)
        return frame

    def _set_context_text(self, frame: QFrame, value: str) -> None:
        labels = frame.findChildren(QLabel)
        if labels:
            labels[-1].setText(value)

    def _update_context_card(self) -> None:
        if not hasattr(self, "context_action"):
            return
        action = "Atualizar bloco existente" if self._is_update_mode() else "Criar bloco novo"
        files = (
            "Nenhum arquivo escolhido"
            if not self.selected_files
            else f"{len(self.selected_files)} arquivo(s): "
            + ", ".join(path.name for path in self.selected_files[:3])
            + ("..." if len(self.selected_files) > 3 else "")
        )
        subject = self.subject_combo.currentText().strip() if hasattr(self, "subject_combo") else ""
        module = self.module_combo.currentText().strip() if hasattr(self, "module_combo") else ""
        if self._is_update_mode():
            block = self._selected_existing_block_title() or "Selecione um bloco"
        else:
            block = self.block_title.text().strip() if hasattr(self, "block_title") else ""
            block = block or "Nome do bloco"
        destination = " > ".join(part for part in [subject or "Materia", module or "Modulo", block] if part)

        if not self._destination_ready(silent=True):
            next_step = "Escolha acao e destino"
        elif not self.selected_files:
            next_step = "Escolha ou arraste arquivos"
        elif not self.prompt_text:
            next_step = "Preparar pacote de estudo"
        elif self.parsed_response is None:
            next_step = "Cole e valide a resposta da IA"
        elif self.current_block is None:
            next_step = "Salvar bloco"
        else:
            next_step = "Abrir resumo ou estudar"

        self._set_context_text(self.context_action, action)
        self._set_context_text(self.context_files, files)
        self._set_context_text(self.context_destination, destination)
        self._set_context_text(self.context_next, next_step)

    def _show_wizard_step(self, index: int) -> None:
        if not hasattr(self, "wizard_stack"):
            return
        index = max(0, min(index, self.wizard_stack.count() - 1))
        self.wizard_stack.setCurrentIndex(index)
        step = index + 1
        current = self.step_states.get(step, "pending")
        if current == "pending":
            self._set_step_status(step, "active")
        self._update_context_card()

    def _wizard_nav(
        self,
        back_text: str,
        next_text: str,
        back_callback: Callable[[], None] | None,
        next_callback: Callable[[], None] | None,
    ) -> QHBoxLayout:
        actions = QHBoxLayout()
        if back_callback is not None:
            back = QPushButton(back_text)
            back.clicked.connect(back_callback)
            actions.addWidget(back)
        actions.addStretch()
        if next_callback is not None:
            next_button = QPushButton(next_text)
            next_button.setObjectName("PrimaryButton")
            next_button.clicked.connect(next_callback)
            actions.addWidget(next_button)
        return actions

    def _build_stepper(self) -> None:
        card = QFrame()
        card.setObjectName("StepCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        steps = [
            (1, "Destino"),
            (2, "Arquivos"),
            (3, "Pacote"),
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

    def _build_destination(self) -> None:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(14)

        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)
        layout.addWidget(label("1. Acao e destino", "SectionTitle"))
        layout.addWidget(label("Defina logo no comeco onde o material sera salvo.", "Muted"))

        action_grid = QGridLayout()
        action_grid.setHorizontalSpacing(12)
        self.action_group = QButtonGroup(self)
        self.action_group.setExclusive(True)
        self.create_action_button = self._action_choice_button(
            "Criar bloco novo",
            "Use para uma aula, apostila ou topico novo.",
            "create",
        )
        self.update_action_button = self._action_choice_button(
            "Atualizar bloco existente",
            "Substitui resumo, flashcards e perguntas de um bloco salvo.",
            "update",
        )
        self.action_group.addButton(self.create_action_button)
        self.action_group.addButton(self.update_action_button)
        self.create_action_button.setChecked(True)
        action_grid.addWidget(self.create_action_button, 0, 0)
        action_grid.addWidget(self.update_action_button, 0, 1)
        layout.addLayout(action_grid)

        self.save_mode_combo = QComboBox()
        self.save_mode_combo.addItem("Criar novo bloco", "create")
        self.save_mode_combo.addItem("Atualizar bloco existente", "update")
        self.save_mode_combo.currentIndexChanged.connect(self._refresh_destination_mode)
        self.save_mode_combo.setVisible(False)
        layout.addWidget(self.save_mode_combo)

        row = QHBoxLayout()
        self.subject_combo = QComboBox()
        self.subject_combo.setEditable(True)
        self.subject_combo.setPlaceholderText("Materia")
        self.subject_combo.currentTextChanged.connect(self._refresh_modules)
        self.subject_combo.currentTextChanged.connect(lambda *_: self._update_context_card())
        self.module_combo = QComboBox()
        self.module_combo.setEditable(True)
        self.module_combo.setPlaceholderText("Modulo")
        self.module_combo.currentTextChanged.connect(self._refresh_existing_blocks)
        self.module_combo.currentTextChanged.connect(lambda *_: self._update_context_card())
        self.block_title = QLineEdit()
        self.block_title.setPlaceholderText("Nome do bloco novo")
        self.block_title.textChanged.connect(lambda *_: self._update_context_card())
        row.addWidget(self.subject_combo)
        row.addWidget(self.module_combo)
        row.addWidget(self.block_title, 1)
        layout.addLayout(row)

        self.existing_block_label = label("Bloco existente", "Weak")
        self.existing_block_combo = QComboBox()
        self.existing_block_combo.setToolTip("Escolha o bloco que recebera o pacote importado.")
        self.existing_block_combo.currentIndexChanged.connect(lambda *_: self._update_context_card())
        layout.addWidget(self.existing_block_label)
        layout.addWidget(self.existing_block_combo)
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Descricao opcional")
        layout.addWidget(self.description_input)
        layout.addLayout(
            self._wizard_nav(
                "",
                "Continuar para arquivos",
                None,
                self._continue_from_destination,
            )
        )
        page_layout.addWidget(card)
        self.wizard_stack.addWidget(page)

    def _action_choice_button(self, title: str, subtitle: str, mode: str) -> QPushButton:
        button = QPushButton(f"{title}\n{subtitle}")
        button.setCheckable(True)
        button.setMinimumHeight(88)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.clicked.connect(lambda checked=False, selected=mode: self._set_action_mode(selected))
        button.setStyleSheet(
            f"""
            QPushButton {{
                text-align: left;
                padding: 16px;
                border-radius: 14px;
                background: {COLORS['card_alt']};
                border: 1px solid {COLORS['border']};
                font-weight: 700;
            }}
            QPushButton:checked {{
                background: {COLORS['accent_dark']};
                border: 1px solid {COLORS['accent']};
            }}
            """
        )
        return button

    def _build_files(self) -> None:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(14)

        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(label("2. Arquivos", "SectionTitle"))
        layout.addWidget(label("Arraste ou selecione PDFs, slides, documentos, texto ou codigo suportado.", "Muted"))
        drop = DropArea()
        drop.files_dropped.connect(self._add_files)
        layout.addWidget(drop)

        actions = QHBoxLayout()
        self.choose_button = QPushButton("Selecionar arquivos")
        self.choose_button.setObjectName("PrimaryButton")
        self.choose_button.clicked.connect(self._choose_files)
        clear = QPushButton("Limpar lista")
        clear.clicked.connect(self._clear_files)
        self.options_button = QPushButton("Opcoes avancadas")
        self.options_button.clicked.connect(self._toggle_options)
        actions.addWidget(self.choose_button)
        actions.addWidget(clear)
        actions.addStretch()
        actions.addWidget(self.options_button)
        layout.addLayout(actions)

        self.file_empty = label("Nenhum arquivo selecionado ainda.", "Muted")
        layout.addWidget(self.file_empty)
        self.file_list = QListWidget()
        self.file_list.setSpacing(8)
        self.file_list.setMinimumHeight(120)
        layout.addWidget(self.file_list)
        self._build_options_panel(layout)
        layout.addLayout(
            self._wizard_nav(
                "Voltar ao destino",
                "Continuar para preparar",
                lambda: self._show_wizard_step(0),
                self._continue_from_files,
            )
        )
        page_layout.addWidget(card)
        self.wizard_stack.addWidget(page)

    def _build_options_panel(self, parent_layout: QVBoxLayout) -> None:
        self.options_panel = QFrame()
        self.options_panel.setObjectName("Panel")
        options_layout = QGridLayout(self.options_panel)
        options_layout.setContentsMargins(14, 12, 14, 12)
        options_layout.setHorizontalSpacing(12)
        options_layout.setVerticalSpacing(10)
        self.flashcard_count = QSpinBox()
        self.flashcard_count.setRange(1, 50)
        self.flashcard_count.setValue(10)
        self.question_count = QSpinBox()
        self.question_count.setRange(1, 50)
        self.question_count.setValue(10)
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["facil", "medio", "dificil"])
        self.difficulty_combo.setCurrentText("medio")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["simples", "academica", "direta para prova"])
        self.language_combo.setCurrentText("direta para prova")
        self.summary_mode_combo = QComboBox()
        self.summary_mode_combo.addItems(["texto + visual avancado", "somente texto", "visual avancado"])
        self.visual_style_combo = QComboBox()
        for label_text, value in VISUAL_STYLE_OPTIONS:
            self.visual_style_combo.addItem(label_text, value)
        fields = [
            ("Flashcards", self.flashcard_count),
            ("Perguntas", self.question_count),
            ("Dificuldade", self.difficulty_combo),
            ("Linguagem", self.language_combo),
            ("Resumo", self.summary_mode_combo),
            ("Estilo visual", self.visual_style_combo),
        ]
        for index, (title, widget) in enumerate(fields):
            options_layout.addWidget(label(title, "Weak"), index // 3 * 2, index % 3)
            options_layout.addWidget(widget, index // 3 * 2 + 1, index % 3)
        self.options_panel.setVisible(False)
        parent_layout.addWidget(self.options_panel)

    def _build_prepare(self) -> None:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(14)

        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)
        layout.addWidget(label("3. Preparar pacote de estudo", "SectionTitle"))
        layout.addWidget(
            label(
                "O LearnKit extrai o texto, gera o prompt, copia para a area de transferencia e abre a IA externa.",
                "Muted",
            )
        )

        provider_row = QHBoxLayout()
        provider_row.addWidget(label("IA externa", "Weak"))
        self.ai_provider_combo = QComboBox()
        for name in AI_PROVIDERS:
            self.ai_provider_combo.addItem(name, AI_PROVIDERS[name])
        provider_row.addWidget(self.ai_provider_combo)
        provider_row.addStretch()
        layout.addLayout(provider_row)

        self.prepare_button = QPushButton("Preparar pacote de estudo")
        self.prepare_button.setObjectName("PrimaryButton")
        self.prepare_button.setMinimumHeight(48)
        self.prepare_button.clicked.connect(self._prepare_study_package)
        layout.addWidget(self.prepare_button)

        self.extract_progress = QProgressBar()
        self.extract_progress.setRange(0, 1)
        self.extract_progress.setValue(0)
        self.extract_progress.setVisible(False)
        layout.addWidget(self.extract_progress)
        self.prepare_status = label("Depois de preparar, cole o prompt na IA e volte com a resposta.", "Muted")
        layout.addWidget(self.prepare_status)

        self.advanced_import_panel = QFrame()
        self.advanced_import_panel.setObjectName("Panel")
        advanced = QVBoxLayout(self.advanced_import_panel)
        advanced.setContentsMargins(14, 12, 14, 12)
        advanced.setSpacing(10)
        manual_actions = QHBoxLayout()
        self.extract_button = QPushButton("Extrair texto")
        self.extract_button.clicked.connect(self._extract_text)
        self.generate_button = QPushButton("Gerar prompt")
        self.generate_button.setEnabled(False)
        self.generate_button.clicked.connect(self._generate_prompt)
        self.copy_button = QPushButton("Copiar prompt")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self._copy_prompt)
        gemini = QPushButton("Abrir Gemini")
        gemini.clicked.connect(self._open_gemini)
        manual_actions.addWidget(self.extract_button)
        manual_actions.addWidget(self.generate_button)
        manual_actions.addWidget(self.copy_button)
        manual_actions.addWidget(gemini)
        manual_actions.addStretch()
        advanced.addLayout(manual_actions)
        self.extraction_stats = label("Nenhum texto extraido ainda.", "Muted")
        advanced.addWidget(self.extraction_stats)
        self.text_preview = QPlainTextEdit()
        self.text_preview.setPlaceholderText("Preview do texto extraido")
        self.text_preview.setMinimumHeight(160)
        advanced.addWidget(self.text_preview)
        self.prompt_preview = QPlainTextEdit()
        self.prompt_preview.setPlaceholderText("Prompt pronto para copiar")
        self.prompt_preview.setMinimumHeight(170)
        advanced.addWidget(self.prompt_preview)
        self.advanced_import_panel.setVisible(False)
        layout.addWidget(self.advanced_import_panel)

        layout.addLayout(
            self._wizard_nav(
                "Voltar aos arquivos",
                "Colar resposta da IA",
                lambda: self._show_wizard_step(1),
                lambda: self._show_wizard_step(3),
            )
        )
        page_layout.addWidget(card)
        self.wizard_stack.addWidget(page)

    def _build_response(self) -> None:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(14)

        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(label("4. Resposta da IA", "SectionTitle"))
        header.addStretch()
        self.paste_response_button = QPushButton("Colar da area de transferencia")
        self.paste_response_button.clicked.connect(self._paste_response_from_clipboard)
        self.validate_button = QPushButton("Validar resposta")
        self.validate_button.setObjectName("PrimaryButton")
        self.validate_button.clicked.connect(self._validate_response)
        header.addWidget(self.paste_response_button)
        header.addWidget(self.validate_button)
        layout.addLayout(header)
        self.ai_response = QPlainTextEdit()
        self.ai_response.setPlaceholderText("Cole aqui o JSON ou Markdown retornado pela IA")
        self.ai_response.setMinimumHeight(220)
        layout.addWidget(self.ai_response)
        self._build_validation_card(layout)
        layout.addLayout(
            self._wizard_nav(
                "Voltar ao pacote",
                "Ir para salvar",
                lambda: self._show_wizard_step(2),
                self._continue_from_response,
            )
        )
        page_layout.addWidget(card)
        self.wizard_stack.addWidget(page)

    def _build_validation_card(self, parent_layout: QVBoxLayout) -> None:
        self.validation_card = QFrame()
        self.validation_card.setObjectName("Panel")
        self.validation_card.setStyleSheet(
            f"QFrame#Panel {{ background: {COLORS['card_alt']}; border: 1px solid {COLORS['border']}; border-radius: 14px; }}"
        )
        layout = QVBoxLayout(self.validation_card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        layout.addWidget(label("Validacao do pacote", "SmallTitle"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        self.validation_summary_text = self._validation_metric("Resumo texto", "nao")
        self.validation_visual_text = self._validation_metric("Resumo visual", "nao")
        self.validation_flashcards_text = self._validation_metric("Flashcards", "0")
        self.validation_questions_text = self._validation_metric("Perguntas", "0")
        self.validation_warnings_text = self._validation_metric("Avisos", "0")
        for index, metric in enumerate(
            [
                self.validation_summary_text,
                self.validation_visual_text,
                self.validation_flashcards_text,
                self.validation_questions_text,
                self.validation_warnings_text,
            ]
        ):
            grid.addWidget(metric, index // 3, index % 3)
        layout.addLayout(grid)
        self.response_status = label("Aguardando resposta da IA.", "Muted")
        layout.addWidget(self.response_status)
        parent_layout.addWidget(self.validation_card)

    def _validation_metric(self, title: str, value: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"background: {COLORS['card']}; border: 1px solid {COLORS['border']}; border-radius: 10px;"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        layout.addWidget(label(title, "Weak"))
        metric = label(value, "SectionTitle")
        layout.addWidget(metric)
        return frame

    def _set_validation_metric(self, frame: QFrame, value: str) -> None:
        labels = frame.findChildren(QLabel)
        if labels:
            labels[-1].setText(value)

    def _build_result(self) -> None:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(14)

        card = panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(label("5. Salvar e abrir", "SectionTitle"))
        self.save_button = QPushButton("Salvar bloco")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.setMinimumHeight(46)
        self.save_button.setEnabled(False)
        self.save_button.setToolTip("Valide a resposta da IA antes de salvar.")
        self.save_button.clicked.connect(self._save_block)
        layout.addWidget(self.save_button)
        self.status = label("Aguardando validacao da resposta.", "Muted")
        layout.addWidget(self.status)

        actions = QHBoxLayout()
        for text, target in [
            ("Abrir resumo", "studies"),
            ("Estudar flashcards", "flashcards"),
            ("Responder perguntas", "questions"),
            ("Ir para modulo", "subjects"),
        ]:
            button = QPushButton(text)
            button.setEnabled(False)
            button.setToolTip("Disponivel depois de salvar o bloco.")
            button.clicked.connect(lambda checked=False, key=target: self._navigate(key))
            self.result_buttons.append(button)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        layout.addLayout(
            self._wizard_nav(
                "Voltar a resposta",
                "",
                lambda: self._show_wizard_step(3),
                None,
            )
        )
        page_layout.addWidget(card)
        self.wizard_stack.addWidget(page)

    def _set_step_status(self, step: int, status: str) -> None:
        self.step_states[step] = status
        badge = self.step_badges.get(step)
        label_widget = self.step_statuses.get(step)
        if badge is None or label_widget is None:
            return
        colors = {
            "pending": COLORS["weak"],
            "active": COLORS["accent"],
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
            f"background: {COLORS['accent_dark'] if status == 'active' else COLORS['card_alt']}; "
            f"border: 1px solid {color}; "
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
        if hasattr(self, "create_action_button"):
            self.create_action_button.setChecked(not update_mode)
            self.update_action_button.setChecked(update_mode)
        if hasattr(self, "save_button"):
            self.save_button.setText("Atualizar bloco" if update_mode else "Salvar bloco")
        self._update_context_card()

    def _is_update_mode(self) -> bool:
        if not hasattr(self, "save_mode_combo"):
            return False
        return self.save_mode_combo.currentData() == "update"

    def _selected_existing_block_title(self) -> str:
        if not hasattr(self, "existing_block_combo"):
            return ""
        data = self.existing_block_combo.currentData()
        return self.existing_block_combo.currentText().strip() if data else ""

    def _set_action_mode(self, mode: str) -> None:
        index = self.save_mode_combo.findData(mode)
        if index >= 0:
            self.save_mode_combo.setCurrentIndex(index)
        self.create_action_button.setChecked(mode == "create")
        self.update_action_button.setChecked(mode == "update")
        self._refresh_destination_mode()
        self._update_context_card()

    def _destination_ready(self, silent: bool = False) -> bool:
        subject_name = self.subject_combo.currentText().strip() if hasattr(self, "subject_combo") else ""
        module_name = self.module_combo.currentText().strip() if hasattr(self, "module_combo") else ""
        title = self.block_title.text().strip() if hasattr(self, "block_title") else ""
        if not subject_name or not module_name:
            if not silent:
                show_toast(self, "Informe materia e modulo antes de continuar.", "warning")
                self._set_step_status(1, "warning")
            return False
        if self._is_update_mode():
            if not self.existing_block_combo.currentData():
                if not silent:
                    show_toast(self, "Selecione o bloco existente que sera atualizado.", "warning")
                    self._set_step_status(1, "warning")
                return False
            return True
        if not title:
            if not silent:
                show_toast(self, "Informe o nome do bloco novo.", "warning")
                self._set_step_status(1, "warning")
            return False
        return True

    def _continue_from_destination(self) -> None:
        if not self._destination_ready():
            return
        self._set_step_status(1, "done")
        self._show_wizard_step(1)

    def _continue_from_files(self) -> None:
        if not self._destination_ready():
            self._show_wizard_step(0)
            return
        if not self.selected_files:
            self._set_step_status(2, "warning")
            show_toast(self, "Escolha pelo menos um arquivo.", "warning")
            return
        self._set_step_status(2, "done")
        self._show_wizard_step(2)

    def _continue_from_response(self) -> None:
        if self.parsed_response is None:
            self._validate_response()
        if self.parsed_response is None:
            return
        self._show_wizard_step(4)

    def _toggle_advanced_import(self) -> None:
        if not hasattr(self, "advanced_import_panel"):
            self._show_wizard_step(2)
            return
        visible = not self.advanced_import_panel.isVisible()
        self.advanced_import_panel.setVisible(visible)
        self.advanced_import_button.setText(
            "Ocultar importacao avancada" if visible else "Importacao avancada"
        )
        if visible:
            self._show_wizard_step(2)

    def _prompt_options(self) -> PromptOptions:
        return PromptOptions(
            flashcard_count=int(self.flashcard_count.value()),
            question_count=int(self.question_count.value()),
            difficulty=self.difficulty_combo.currentText(),
            language_style=self.language_combo.currentText(),
            summary_mode=self.summary_mode_combo.currentText(),
            visual_style=str(self.visual_style_combo.currentData() or "auto"),
        )

    def _prepare_study_package(self) -> None:
        if not self._destination_ready():
            self._show_wizard_step(0)
            return
        if not self.selected_files:
            self._set_step_status(2, "warning")
            show_toast(self, "Escolha ou arraste pelo menos um arquivo.", "warning")
            self._show_wizard_step(1)
            return
        self.prepare_after_extraction = True
        set_button_loading(self.prepare_button, True, "Preparando...")
        self.prepare_status.setText("Extraindo texto dos arquivos...")
        if self.extraction_result and self.extraction_result.combined_content.text.strip():
            self._finish_prepare_study_package()
            return
        self._extract_text()

    def _finish_prepare_study_package(self) -> None:
        self.prepare_after_extraction = False
        if not self.extraction_result or not self.extraction_result.combined_content.text.strip():
            set_button_loading(self.prepare_button, False)
            self.prepare_status.setText("Nao foi possivel extrair texto suficiente dos arquivos.")
            self._set_step_status(3, "error")
            return
        self._generate_prompt()
        self._copy_prompt()
        self._open_external_ai()
        set_button_loading(self.prepare_button, False)
        self.prepare_status.setText(
            "Prompt copiado. Cole na IA aberta no navegador, aguarde a resposta e volte para colar no LearnKit."
        )
        self._set_step_status(3, "done")
        self._update_context_card()

    def _open_external_ai(self) -> None:
        url = str(self.ai_provider_combo.currentData() or AI_PROVIDERS["Gemini"])
        webbrowser.open(url)
        show_toast(self, "IA externa aberta no navegador.", "info")
        log_action("external_ai_opened", url=url)

    def _paste_response_from_clipboard(self) -> None:
        text = QApplication.clipboard().text()
        if not text.strip():
            show_toast(self, "A area de transferencia esta vazia.", "warning")
            return
        self.ai_response.setPlainText(text)
        show_toast(self, "Resposta colada. Agora valide o pacote.", "success")
        log_action("ai_response_pasted", chars=len(text))

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
        self._set_step_status(2, "done")
        self._update_context_card()
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
        self._set_step_status(2, "pending")
        self._set_step_status(3, "pending")
        self._set_step_status(4, "pending")
        self._set_step_status(5, "pending")
        self._set_step_status(6, "pending")
        self._update_context_card()
        show_toast(self, "Lista de arquivos limpa.", "info")

    def _remove_file(self, path: Path) -> None:
        self.selected_files = [item for item in self.selected_files if item != path]
        self.file_statuses.pop(str(path), None)
        self._reset_outputs_after_file_change()
        self._render_file_list()
        self._set_step_status(2, "done" if self.selected_files else "pending")
        self._update_context_card()
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
        for step in (3, 4, 5, 6):
            self._set_step_status(step, "pending")
        self._update_context_card()

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
            self._set_step_status(2, "warning")
            return
        self._set_step_status(3, "active")
        for file in self.selected_files:
            self.file_statuses[str(file)] = ("extraindo", "")
        self._render_file_list()
        set_button_loading(self.extract_button, True, "Extraindo...")
        if self.prepare_after_extraction and hasattr(self, "prepare_button"):
            set_button_loading(self.prepare_button, True, "Preparando...")
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
            self._set_step_status(3, "error")
            show_toast(self, "Nao foi possivel extrair texto dos arquivos.", "error")
        elif warnings or failures:
            self._set_step_status(3, "warning")
            show_toast(self, "Texto extraido com avisos. Confira o preview.", "warning")
        else:
            self._set_step_status(3, "done")
            show_toast(self, "Texto extraido com sucesso.", "success")
        log_action(
            "extraction_finished",
            files=len(result.files),
            chars=result.combined_content.character_count,
            warnings=len(warnings),
            failures=len(failures),
        )
        self._update_context_card()
        if self.prepare_after_extraction:
            self._finish_prepare_study_package()

    def _extraction_failed(self, message: str) -> None:
        self._reset_extraction_button()
        self._set_step_status(3, "error")
        self.prepare_after_extraction = False
        if hasattr(self, "prepare_button"):
            set_button_loading(self.prepare_button, False)
        show_toast(self, f"Erro na extracao: {message}", "error")
        log_action("extraction_failed", error=message)

    def _reset_extraction_button(self) -> None:
        self.extract_progress.setVisible(False)
        self.extract_progress.setRange(0, 1)
        set_button_loading(self.extract_button, False)

    def _toggle_options(self) -> None:
        visible = not self.options_panel.isVisible()
        self.options_panel.setVisible(visible)
        self.options_button.setText("Ocultar opcoes" if visible else "Opcoes avancadas")

    def _generate_prompt(self) -> None:
        if not self.extraction_result or not self.extraction_result.combined_content.text.strip():
            show_toast(self, "Extraia o texto antes de gerar o prompt.", "warning")
            self._set_step_status(3, "warning")
            return
        options = self._prompt_options()
        subject = self.subject_combo.currentText().strip() or "Materia a definir"
        module = self.module_combo.currentText().strip() or "Modulo a definir"
        block = (
            self._selected_existing_block_title()
            if self._is_update_mode()
            else self.block_title.text().strip()
        ) or "Bloco de estudo a definir"
        self.prompt_text = self.generate_prompt_use_case.execute(
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
        self._update_context_card()

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
        parsed = self.parse_ai_response_use_case.execute(raw)
        has_summary = bool(parsed.summary_text.strip())
        has_visual = bool(parsed.summary_visual.strip())
        has_content = has_summary or has_visual or bool(parsed.flashcards) or bool(parsed.questions)
        if not has_content:
            self.parsed_response = None
            self.save_button.setEnabled(False)
            self._set_step_status(4, "error")
            self._set_validation_metric(self.validation_summary_text, "nao")
            self._set_validation_metric(self.validation_visual_text, "nao")
            self._set_validation_metric(self.validation_flashcards_text, str(len(parsed.flashcards)))
            self._set_validation_metric(self.validation_questions_text, str(len(parsed.questions)))
            self._set_validation_metric(self.validation_warnings_text, str(len(parsed.parser_warnings)))
            self.response_status.setText("Não foi possível identificar conteúdo válido na resposta.")
            self.response_status.setText(
                "Nao encontrei resumo, flashcards ou perguntas. Confira se voce colou a resposta completa da IA."
            )
            show_toast(self, "Resposta sem resumo, flashcards ou perguntas reconheciveis.", "error")
            log_action("ai_response_validation_failed", warnings=len(parsed.parser_warnings))
            self._update_context_card()
            return

        self.parsed_response = parsed
        self.response_status.setText(
            f"Resumo texto: {'sim' if has_summary else 'nao'} - "
            f"Resumo visual: {'sim' if has_visual else 'nao'} - "
            f"{len(parsed.flashcards)} flashcards - {len(parsed.questions)} perguntas - "
            f"{len(parsed.parser_warnings)} avisos"
        )
        self._set_validation_metric(self.validation_summary_text, "sim" if has_summary else "nao")
        self._set_validation_metric(self.validation_visual_text, "sim" if has_visual else "nao")
        self._set_validation_metric(self.validation_flashcards_text, str(len(parsed.flashcards)))
        self._set_validation_metric(self.validation_questions_text, str(len(parsed.questions)))
        self._set_validation_metric(self.validation_warnings_text, str(len(parsed.parser_warnings)))
        if parsed.parser_warnings:
            self.response_status.setText(
                "Pacote aproveitavel, mas revise os avisos: " + "; ".join(parsed.parser_warnings[:3])
            )
        else:
            self.response_status.setText("Pacote validado. Tudo pronto para salvar o bloco.")
        self.save_button.setEnabled(True)
        self.save_button.setToolTip("")
        self._set_step_status(4, "warning" if parsed.parser_warnings else "done")
        show_toast(self, "Resposta validada. Agora salve o bloco.", "success")
        log_action(
            "ai_response_validated",
            flashcards=len(parsed.flashcards),
            questions=len(parsed.questions),
            warnings=len(parsed.parser_warnings),
        )
        self._update_context_card()

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
            result = self.import_package_use_case.execute(
                StudyPackageImportDTO(
                    extraction=self.extraction_result,
                    generated_prompt=self.prompt_preview.toPlainText(),
                    raw_ai_response=self.ai_response.toPlainText(),
                    package=self.parsed_response,
                    destination=ImportDestinationDTO(
                        subject_name=subject_name,
                        module_name=module_name,
                        block_title=title,
                        existing_block_id=str(existing_block_id) if existing_block_id else None,
                        description=description,
                    ),
                    mode="update" if update_mode else "create",
                )
            )
            block = result.block
            action_text = "atualizado" if update_mode else "criado"
            toast_text = (
                "Bloco de estudo atualizado com sucesso."
                if update_mode
                else "Bloco de estudo salvo com sucesso."
            )
            log_name = "import_package_updated" if update_mode else "import_package_saved"
            if result.created_subject:
                log_action("subject_created_from_import", subject=result.subject_name)
            if result.created_module:
                log_action("module_created_from_import", subject=result.subject_name, module=result.module_name)
            self.current_block = block
            self._set_step_status(5, "done")
            self._set_step_status(6, "done")
            for button in self.result_buttons:
                button.setEnabled(True)
                button.setToolTip("")
            self.status.setText(
                f"Bloco {action_text}: {result.subject_name} > {result.module_name} > {block.title}. "
                f"{len(block.flashcards)} flashcards e {len(block.questions)} perguntas."
            )
            flash_button_success(self.save_button, "Salvo!")
            show_toast(self, toast_text, "success")
            log_action(
                log_name,
                block_id=block.id,
                subject=result.subject_name,
                module=result.module_name,
                flashcards=len(block.flashcards),
                questions=len(block.questions),
            )
            self.refresh()
            self._update_context_card()
        except Exception as exc:
            set_button_loading(self.save_button, False)
            self._set_step_status(5, "error")
            show_toast(self, f"Erro ao salvar bloco: {exc}", "error")
            log_action("import_package_save_failed", error=str(exc))

    def _navigate(self, key: str) -> None:
        window = self.window()
        if self.current_block and key == "subjects" and hasattr(window, "open_subject"):
            context = self.study_session_query_service.block_context(self.current_block.id)
            window.open_subject(context.subject.name, context.module.name)
        elif self.current_block and hasattr(window, "open_block"):
            window.open_block(self.current_block.id, key)
        elif hasattr(window, "navigate"):
            window.navigate(key)
