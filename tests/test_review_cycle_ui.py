import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def _qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def _scheduled_block(tmp_path: Path):
    from app.application.use_cases.manage_review_cycle import ManageReviewCycleUseCase
    from app.core.database import SQLiteStorage
    from app.core.models.flashcard import Flashcard
    from app.core.models.question import Question
    from app.core.models.summary import Summary

    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Estrutura de Dados")
    module = storage.create_module(subject.slug, "Grafos")
    block = storage.create_block(subject.slug, module.slug, "BFS e DFS")
    block.summary = Summary("Resumo curto sobre busca em grafos.")
    block.flashcards = [Flashcard("O que e BFS?", "Busca em largura.")]
    block.questions = [
        Question("BFS usa qual estrutura?", {"A": "Fila", "B": "Pilha", "C": "Heap", "D": "Set"}, "A")
    ]
    storage.save_block(subject, module, block)
    cycle = ManageReviewCycleUseCase(storage).activate_cycle(
        block.id,
        studied_at=datetime(2026, 5, 23, 12, 0, tzinfo=timezone.utc),
    )
    return storage, block, cycle.schedules[0]


def test_settings_page_exposes_review_cycle_defaults_and_persists_preference(tmp_path, monkeypatch) -> None:
    _qapp()
    from app.core.database import SQLiteStorage
    import app.ui.pages.settings_page as settings_module
    from app.ui.pages.settings_page import SettingsPage

    monkeypatch.setattr(settings_module, "show_toast", lambda *args, **kwargs: None)
    page = SettingsPage(SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False))

    assert page.review_cycle_enabled.isChecked() is False
    assert page.review_step_1h_enabled.isChecked() is True
    page.review_cycle_enabled.setChecked(True)
    page.preferred_review_time.setText("20:00")
    page._save_settings()

    settings = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert settings["review_cycle_enabled"] is True
    assert settings["preferred_review_time"] == "20:00"


def test_reviews_page_renders_separate_review_queue_and_actions(tmp_path: Path) -> None:
    _qapp()
    from PySide6.QtWidgets import QLabel

    from app.application.query_services.ui_data_provider import UIDataProvider
    from app.ui.pages.reviews_page import ReviewsPage

    storage, block, schedule = _scheduled_block(tmp_path)
    page = ReviewsPage(UIDataProvider(storage), storage)
    texts = [item.text() for item in page.findChildren(QLabel)]

    assert "Fila de Revisões" in texts
    assert block.title in texts
    page._mark_done(schedule.id)
    assert storage.get_review_schedule(schedule.id).status == "done"


def test_review_session_dialog_builds_active_content_without_crashing(tmp_path: Path) -> None:
    _qapp()
    from PySide6.QtWidgets import QLabel

    from app.ui.pages.reviews_page import ReviewSessionDialog

    storage, _block, schedule = _scheduled_block(tmp_path)
    dialog = ReviewSessionDialog(storage, schedule.id)
    texts = [item.text() for item in dialog.findChildren(QLabel)]

    assert any("BFS e DFS" in text for text in texts)
    assert any("O que e BFS?" in text for text in texts)


def test_review_session_dialog_paints_window_and_footer_with_theme_background_when_resized(tmp_path: Path) -> None:
    app = _qapp()

    from app.ui.pages.reviews_page import ReviewSessionDialog
    from app.ui.theme import COLORS, apply_app_theme

    apply_app_theme(app)
    storage, _block, schedule = _scheduled_block(tmp_path)
    dialog = ReviewSessionDialog(storage, schedule.id)
    dialog.show()
    expected = COLORS["background"].lower()
    for width, height in ((1366, 768), (920, 560)):
        dialog.resize(width, height)
        app.processEvents()
        image = dialog.grab().toImage()
        assert image.pixelColor(1, 1).name().lower() == expected
        assert image.pixelColor(dialog.width() // 2, dialog.height() - 10).name().lower() == expected
    dialog.close()


def test_home_displays_review_cycle_notification_card(tmp_path: Path) -> None:
    _qapp()
    from PySide6.QtWidgets import QLabel

    from app.application.query_services.ui_data_provider import UIDataProvider
    from app.ui.pages.home_page import HomePage

    storage, _block, _schedule = _scheduled_block(tmp_path)
    page = HomePage(UIDataProvider(storage))
    texts = [item.text() for item in page.findChildren(QLabel)]

    assert "Revisões de Hoje" in texts
    assert any("atrasadas" in text for text in texts)


def test_studies_allows_manual_cycle_when_global_creation_is_disabled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _qapp()
    from PySide6.QtWidgets import QPushButton

    from app.application.query_services.ui_data_provider import UIDataProvider
    from app.core.database import SQLiteStorage
    import app.ui.pages.studies_page as studies_module
    from app.ui.pages.studies_page import StudiesPage

    monkeypatch.setattr(studies_module, "show_toast", lambda *args, **kwargs: None)
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Banco de Dados")
    module = storage.create_module(subject.slug, "SQL")
    block = storage.create_block(subject.slug, module.slug, "Normalização")
    page = StudiesPage(
        UIDataProvider(storage),
        storage,
        settings_provider=lambda: {"review_cycle_enabled": False},
    )
    activate = next(
        button
        for button in page.findChildren(QPushButton)
        if button.text() == "Ativar Ciclo de Revisão"
    )

    activate.click()

    assert len(storage.list_review_schedules(block.id)) == 4
