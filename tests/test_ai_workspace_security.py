from __future__ import annotations

import os
import sys


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu --no-sandbox")


def _qapp():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def test_workspace_dialog_is_deleted_when_closed(monkeypatch) -> None:
    app = _qapp()
    from PySide6.QtCore import QCoreApplication, QEvent, Qt
    import shiboken6

    from app.application.dto.ai_provider import get_ai_provider
    import app.ui.pages.ai_workspace_dialog as workspace_module

    monkeypatch.setattr(workspace_module, "QWebEngineView", None)
    dialog = workspace_module.AIWorkspaceDialog(
        get_ai_provider("gemini"),
        "prompt",
    )

    assert dialog.testAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    dialog.show()
    dialog.close()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()

    assert not shiboken6.isValid(dialog)


def test_workspace_external_browser_failure_is_reported(monkeypatch) -> None:
    _qapp()
    from app.application.dto.ai_provider import get_ai_provider
    import app.ui.pages.ai_workspace_dialog as workspace_module

    monkeypatch.setattr(workspace_module, "QWebEngineView", None)
    monkeypatch.setattr(workspace_module.webbrowser, "open", lambda url: False)
    messages: list[tuple[str, str]] = []
    monkeypatch.setattr(
        workspace_module,
        "show_toast",
        lambda parent, message, kind="info": messages.append((message, kind)),
    )
    dialog = workspace_module.AIWorkspaceDialog(get_ai_provider("claude"), "prompt")

    assert dialog._open_external() is False
    assert messages and messages[-1][1] == "error"


def test_web_profiles_are_off_record_and_isolated_per_workspace() -> None:
    _qapp()
    from PySide6.QtCore import QObject
    from PySide6.QtWebEngineCore import QWebEngineProfile

    import app.ui.pages.ai_workspace_dialog as workspace_module

    assert hasattr(workspace_module, "_create_isolated_profile")
    owner_one = QObject()
    owner_two = QObject()
    profile_one = workspace_module._create_isolated_profile(owner_one)
    profile_two = workspace_module._create_isolated_profile(owner_two)

    assert profile_one is not profile_two
    assert profile_one.isOffTheRecord()
    assert profile_two.isOffTheRecord()
    assert (
        profile_one.persistentCookiesPolicy()
        == QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
    )


def test_web_page_blocks_unsafe_schemes_and_popups() -> None:
    _qapp()
    from PySide6.QtCore import QObject, QUrl
    from PySide6.QtWebEngineCore import QWebEnginePage

    import app.ui.pages.ai_workspace_dialog as workspace_module

    assert hasattr(workspace_module, "IsolatedAIWebPage")
    owner = QObject()
    profile = workspace_module._create_isolated_profile(owner)
    page = workspace_module.IsolatedAIWebPage(profile, "gemini", owner)

    assert page.acceptNavigationRequest(
        QUrl("https://gemini.google.com/"),
        QWebEnginePage.NavigationType.NavigationTypeTyped,
        True,
    )
    assert not page.acceptNavigationRequest(
        QUrl("file:///C:/secret.txt"),
        QWebEnginePage.NavigationType.NavigationTypeLinkClicked,
        True,
    )
    assert not page.acceptNavigationRequest(
        QUrl("javascript:alert(1)"),
        QWebEnginePage.NavigationType.NavigationTypeLinkClicked,
        True,
    )
    assert page.createWindow(QWebEnginePage.WebWindowType.WebBrowserTab) is None
