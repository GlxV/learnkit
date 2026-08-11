from __future__ import annotations

import webbrowser

from PySide6.QtCore import QObject, QUrl, Qt
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
    from PySide6.QtWebEngineCore import (
        QWebEnginePage,
        QWebEngineProfile,
        QWebEngineSettings,
    )
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:  # pragma: no cover - depends on the installed Qt distribution
    QWebEnginePage = None  # type: ignore[assignment,misc]
    QWebEngineProfile = None  # type: ignore[assignment,misc]
    QWebEngineSettings = None  # type: ignore[assignment,misc]
    QWebEngineView = None  # type: ignore[assignment,misc]


def embedded_workspace_available() -> bool:
    return QWebEngineView is not None and QWebEngineProfile is not None


def _create_isolated_profile(parent: QObject):
    if QWebEngineProfile is None:
        raise RuntimeError("QtWebEngine nao esta disponivel.")
    profile = QWebEngineProfile(parent)
    profile.setPersistentCookiesPolicy(
        QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
    )
    profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
    return profile


if QWebEnginePage is not None:

    class IsolatedAIWebPage(QWebEnginePage):
        """Web page limited to HTTPS navigation without popups."""

        def __init__(self, profile, provider_key: str, parent: QObject | None = None) -> None:
            super().__init__(profile, parent)
            self.provider_key = provider_key

        def acceptNavigationRequest(self, url, navigation_type, is_main_frame):  # type: ignore[override]
            _ = navigation_type, is_main_frame
            scheme = url.scheme().lower()
            allowed = scheme in {"https", "about"}
            if not allowed:
                log_action(
                    "ai_workspace_navigation_blocked",
                    provider=self.provider_key,
                    scheme=scheme or "unknown",
                )
            return allowed

        def createWindow(self, window_type):  # type: ignore[override]
            _ = window_type
            log_action("ai_workspace_popup_blocked", provider=self.provider_key)
            return None

else:  # pragma: no cover - only used when QtWebEngine is not installed
    IsolatedAIWebPage = None  # type: ignore[assignment,misc]


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
        self.web_profile = None
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
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
        if embedded_workspace_available():
            self.web_view = QWebEngineView()
            self.web_profile = _create_isolated_profile(self)
            self.web_profile.downloadRequested.connect(self._deny_download)
            page = IsolatedAIWebPage(self.web_profile, provider.key, self.web_view)
            page.permissionRequested.connect(self._deny_permission)
            self.web_view.setPage(page)
            settings = self.web_view.settings()
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls,
                False,
            )
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
                False,
            )
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard,
                False,
            )
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows,
                False,
            )
            settings.setUnknownUrlSchemePolicy(
                QWebEngineSettings.UnknownUrlSchemePolicy.DisallowUnknownUrlSchemes
            )
            self.web_view.setUrl(QUrl(provider.url))
            splitter.addWidget(self.web_view)
        else:
            fallback = panel()
            fallback_layout = QVBoxLayout(fallback)
            fallback_layout.setContentsMargins(18, 18, 18, 18)
            fallback_layout.addStretch()
            fallback_title = QLabel("WebView indisponível nesta instalação")
            fallback_title.setStyleSheet(
                f"font-size: 18px; font-weight: 800; color: {COLORS['text']};"
            )
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

    def _copy_prompt(self) -> bool:
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.prompt)
            if clipboard.text() != self.prompt:
                raise OSError("a area de transferencia nao confirmou o conteudo")
        except Exception as exc:
            show_toast(self, f"Nao foi possivel copiar o prompt: {exc}", "error")
            log_action(
                "ai_workspace_prompt_copy_failed",
                provider=self.provider.key,
                error=str(exc),
            )
            return False
        flash_button_success(self.copy_button, "Copiado!")
        show_toast(self, "Prompt copiado para a área de transferência.", "success")
        log_action("ai_workspace_prompt_copied", provider=self.provider.key, chars=len(self.prompt))
        return True

    def _open_external(self) -> bool:
        try:
            opened = webbrowser.open(self.provider.url)
        except Exception as exc:
            show_toast(self, f"Nao foi possivel abrir o provider: {exc}", "error")
            log_action(
                "ai_workspace_external_open_failed",
                provider=self.provider.key,
                error=str(exc),
            )
            return False
        if not opened:
            show_toast(self, "Nao foi possivel abrir o provider no navegador.", "error")
            log_action("ai_workspace_external_open_failed", provider=self.provider.key)
            return False
        show_toast(self, "Provider aberto no navegador.", "info")
        log_action("ai_workspace_external_opened", provider=self.provider.key, url=self.provider.url)
        return True

    def _deny_download(self, download) -> None:
        download.cancel()
        show_toast(self, "Downloads foram bloqueados no workspace experimental.", "warning")
        log_action("ai_workspace_download_blocked", provider=self.provider.key)

    def _deny_permission(self, permission) -> None:
        permission.deny()
        show_toast(self, "Permissao do site negada no workspace experimental.", "warning")
        log_action("ai_workspace_permission_denied", provider=self.provider.key)
