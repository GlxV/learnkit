from __future__ import annotations

import os
import sys
import threading
from pathlib import Path


def _qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def _wait_until(predicate, timeout_ms: int = 3000) -> bool:
    from PySide6.QtTest import QTest

    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        QTest.qWait(10)
        elapsed += 10
    return predicate()


def _result(text: str):
    from app.core.extractors.file_extractor import FileExtractionResult
    from app.core.models.extracted_content import ExtractedContent

    return FileExtractionResult(combined_content=ExtractedContent(text=text))


def _page(tmp_path: Path, monkeypatch):
    _qapp()
    from app.core.database.sqlite_storage import SQLiteStorage
    import app.ui.pages.import_page as import_page_module
    from app.ui.pages.import_page import ImportPage

    monkeypatch.setattr(import_page_module, "show_toast", lambda *args, **kwargs: None)
    return ImportPage([], SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False))


def test_extraction_result_is_ignored_after_selected_files_change(tmp_path, monkeypatch) -> None:
    from app.core.extractors.file_extractor import FileExtractor

    page = _page(tmp_path, monkeypatch)
    material = tmp_path / "material.txt"
    material.write_text("novo", encoding="utf-8")
    started = threading.Event()
    release = threading.Event()

    def slow_extract(self, files):
        started.set()
        assert release.wait(3)
        return _result("CONTEUDO ANTIGO")

    monkeypatch.setattr(FileExtractor, "extract_files", slow_extract)
    page._add_files([material])
    page._extract_text()
    assert _wait_until(started.is_set)

    page._clear_files()
    release.set()
    assert _wait_until(lambda: not page.has_active_extraction())

    assert page.extraction_result is None
    assert page.text_preview.toPlainText() == ""
    assert not page.generate_button.isEnabled()


def test_duplicate_extraction_request_does_not_start_second_worker(tmp_path, monkeypatch) -> None:
    from app.core.extractors.file_extractor import FileExtractor

    page = _page(tmp_path, monkeypatch)
    material = tmp_path / "material.txt"
    material.write_text("texto", encoding="utf-8")
    started = threading.Event()
    release = threading.Event()
    calls = 0

    def slow_extract(self, files):
        nonlocal calls
        calls += 1
        started.set()
        assert release.wait(3)
        return _result("texto")

    monkeypatch.setattr(FileExtractor, "extract_files", slow_extract)
    page._add_files([material])
    page._extract_text()
    assert _wait_until(started.is_set)

    page._extract_text()
    release.set()
    assert _wait_until(lambda: not page.has_active_extraction())

    assert calls == 1


def test_external_browser_failure_is_reported(tmp_path, monkeypatch) -> None:
    import app.ui.pages.import_page as import_page_module

    page = _page(tmp_path, monkeypatch)
    messages: list[tuple[str, str]] = []
    monkeypatch.setattr(import_page_module.webbrowser, "open", lambda url: False)
    monkeypatch.setattr(
        import_page_module,
        "show_toast",
        lambda parent, message, kind="info": messages.append((message, kind)),
    )

    assert page._open_external_ai() is False
    assert messages and messages[-1][1] == "error"


def test_clipboard_failure_stops_prepare_handoff(tmp_path, monkeypatch) -> None:
    import app.ui.pages.import_page as import_page_module

    page = _page(tmp_path, monkeypatch)
    page.prompt_preview.setPlainText("prompt")
    messages: list[tuple[str, str]] = []

    class FailingClipboard:
        def setText(self, text: str) -> None:
            raise OSError("clipboard indisponivel")

    class FakeApplication:
        @staticmethod
        def clipboard():
            return FailingClipboard()

    monkeypatch.setattr(import_page_module, "QApplication", FakeApplication)
    monkeypatch.setattr(
        import_page_module,
        "show_toast",
        lambda parent, message, kind="info": messages.append((message, kind)),
    )

    assert page._copy_prompt() is False
    assert messages and messages[-1][1] == "error"


def test_main_window_refuses_to_close_during_extraction(tmp_path, monkeypatch) -> None:
    _qapp()
    from PySide6.QtGui import QCloseEvent
    from PySide6.QtWidgets import QMessageBox

    from app.ui.main_window import MainWindow

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
    window = MainWindow()
    import_page = window.pages["import"]
    monkeypatch.setattr(import_page, "has_active_extraction", lambda: True)
    event = QCloseEvent()
    event.accept()

    window.closeEvent(event)

    assert not event.isAccepted()
    monkeypatch.setattr(import_page, "has_active_extraction", lambda: False)
    window.close()
