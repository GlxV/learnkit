from __future__ import annotations

import webbrowser

from PySide6.QtCore import QUrl, Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.application.dto.ai_provider import AIProviderDTO
from app.ui.feedback import flash_button_success, log_action, show_toast
from app.ui.pages.base import panel
from app.ui.theme import COLORS

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:  # pragma: no cover - depends on the installed Qt distribution
    QWebEngineView = None  # type: ignore[assignment,misc]


def embedded_workspace_available() -> bool:
    return QWebEngineView is not None


class AIWorkspaceDialog(QDialog):
    """Experimental provider workspace with a safe external-browser fallback."""

    def __init__(
        self,
        provider: AIProviderDTO,
        prompt: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.provider = provider
        self.prompt = prompt
        self.setWindowTitle(f"Workspace IA experimental - {provider.label}")
        self.resize(1440, 860)
        self.setObjectName("AIWorkspaceDialog")
        self.setStyleSheet(
            f"QDialog#AIWorkspaceDialog {{ background: {COLORS['background']}; }}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel(f"Workspace IA · {provider.label}")
        title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {COLORS['text']};")
        header.addWidget(title)
        header.addStretch()
        self.backend_label = QLabel(
            "WebView experimental" if embedded_workspace_available() else "Navegador externo"
        )
        self.backend_label.setStyleSheet(f"color: {COLORS['muted']};")
        header.addWidget(self.backend_label)
        root.addLayout(header)

        note = QLabel(
            "O LearnKit não injeta credenciais nem envia o prompt automaticamente. "
            "Copie o prompt, use a sessão da sua conta e cole a resposta de volta no passo 4."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {COLORS['muted']};")
        root.addWidget(note)

        splitter = QSplitter()
        prompt_panel = panel()
        prompt_layout = QVBoxLayout(prompt_panel)
        prompt_layout.setContentsMargins(12, 12, 12, 12)
        prompt_layout.addWidget(QLabel("Prompt pronto"))
        self.prompt_preview = QPlainTextEdit()
        self.prompt_preview.setPlainText(prompt)
        self.prompt_preview.setReadOnly(True)
        prompt_layout.addWidget(self.prompt_preview, 1)
        self.copy_button = QPushButton("Copiar prompt")
        self.copy_button.setObjectName("PrimaryButton")
        self.copy_button.clicked.connect(self._copy_prompt)
        prompt_layout.addWidget(self.copy_button)
        splitter.addWidget(prompt_panel)

        self.web_view = None
        if QWebEngineView is not None:
            self.web_view = QWebEngineView()
            self.web_view.setUrl(QUrl(provider.url))
            splitter.addWidget(self.web_view)
        else:
            fallback = panel()
            fallback_layout = QVBoxLayout(fallback)
            fallback_layout.setContentsMargins(18, 18, 18, 18)
            fallback_layout.addStretch()
            fallback_title = QLabel("WebView indisponível nesta instalação")
            fallback_title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {COLORS['text']};")
            fallback_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_layout.addWidget(fallback_title)
            fallback_note = QLabel("Abra o provider no navegador padrão para continuar.")
            fallback_note.setWordWrap(True)
            fallback_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_layout.addWidget(fallback_note)
            open_fallback = QPushButton("Abrir no navegador")
            open_fallback.setObjectName("PrimaryButton")
            open_fallback.clicked.connect(self._open_external)
            fallback_layout.addWidget(open_fallback)
            fallback_layout.addStretch()
            splitter.addWidget(fallback)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, 1)

        actions = QHBoxLayout()
        actions.addStretch()
        self.external_button = QPushButton("Abrir no navegador")
        self.external_button.clicked.connect(self._open_external)
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.close)
        actions.addWidget(self.external_button)
        actions.addWidget(close_button)
        root.addLayout(actions)

    def _copy_prompt(self) -> None:
        QApplication.clipboard().setText(self.prompt)
        flash_button_success(self.copy_button, "Copiado!")
        show_toast(self, "Prompt copiado para a área de transferência.", "success")
        log_action("ai_workspace_prompt_copied", provider=self.provider.key, chars=len(self.prompt))

    def _open_external(self) -> None:
        webbrowser.open(self.provider.url)
        show_toast(self, "Provider aberto no navegador.", "info")
        log_action("ai_workspace_external_opened", provider=self.provider.key, url=self.provider.url)
