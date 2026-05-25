from __future__ import annotations

import os
import sys
from pathlib import Path


def _qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    app.flush_deleted_widgets = lambda: QCoreApplication.sendPostedEvents(
        None, QEvent.Type.DeferredDelete
    )
    return app


def _blocks(tmp_path: Path):
    from app.core.database import SQLiteStorage
    from app.core.models.flashcard import Flashcard
    from app.core.models.question import Question
    from app.core.models.summary import Summary

    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Algoritmos")
    module = storage.create_module(subject.slug, "Prova 1")
    first = storage.create_block(subject.slug, module.slug, "Arrays")
    second = storage.create_block(subject.slug, module.slug, "Listas")
    for block in (first, second):
        block.summary = Summary(f"Resumo de {block.title}.")
        block.flashcards = [Flashcard("Pergunta comum?", "Resposta comum.")]
        block.questions = [
            Question("Questao comum?", {"A": "Certa", "B": "Errada", "C": "-", "D": "-"}, "A")
        ]
        storage.save_block(subject, module, block)
    return storage, first, second


def test_studies_page_selects_multiple_blocks_and_can_clear_selection(tmp_path: Path) -> None:
    app = _qapp()
    from PySide6.QtWidgets import QPushButton

    from app.application.query_services.ui_data_provider import UIDataProvider
    from app.ui.pages.studies_page import StudiesPage

    storage, _first, _second = _blocks(tmp_path)
    page = StudiesPage(UIDataProvider(storage), storage)
    page.show()
    app.processEvents()

    selectors = [
        button
        for button in page.findChildren(QPushButton)
        if button.text() == "Selecionar" and button.isVisible()
    ]
    assert len(selectors) == 2
    selectors[0].click()
    app.processEvents()
    app.flush_deleted_widgets()
    next_selector = next(
        button
        for button in page.findChildren(QPushButton)
        if button.text() == "Selecionar" and button.isVisible()
    )
    next_selector.click()
    app.processEvents()
    app.flush_deleted_widgets()

    review = next(
        button
        for button in page.findChildren(QPushButton)
        if button.text() == "Revisar selecionados (2)" and button.isVisible()
    )
    assert review.isEnabled()
    clear = next(
        button
        for button in page.findChildren(QPushButton)
        if button.text() == "Limpar seleção" and button.isVisible()
    )
    clear.click()
    app.processEvents()
    app.flush_deleted_widgets()
    assert page.selected_review_block_ids == set()
    assert not any(
        button.isVisible() and button.text().startswith("Revisar selecionados")
        for button in page.findChildren(QPushButton)
    )
    page.close()


def test_studies_page_clears_combined_selection_when_scope_changes_or_page_is_hidden(
    tmp_path: Path,
) -> None:
    app = _qapp()
    from PySide6.QtWidgets import QPushButton

    from app.application.query_services.ui_data_provider import UIDataProvider
    from app.ui.pages.studies_page import StudiesPage

    storage, _first, _second = _blocks(tmp_path)
    subject = storage.get_subject("Algoritmos")
    other_module = storage.create_module(subject.slug, "Prova 2")
    storage.create_block(subject.slug, other_module.slug, "Pilhas")
    page = StudiesPage(UIDataProvider(storage), storage)
    page.show()
    app.processEvents()

    selector = next(
        button
        for button in page.findChildren(QPushButton)
        if button.text() == "Selecionar" and button.isVisible()
    )
    selector.click()
    app.processEvents()
    assert page.selected_review_block_ids
    page.module_combo.setCurrentText("Prova 2")
    app.processEvents()
    app.flush_deleted_widgets()
    assert page.selected_review_block_ids == set()

    selector = next(
        button
        for button in page.findChildren(QPushButton)
        if button.text() == "Selecionar" and button.isVisible()
    )
    selector.click()
    app.processEvents()
    assert page.selected_review_block_ids
    page.hide()
    app.processEvents()
    assert page.selected_review_block_ids == set()


def test_combined_review_dialog_applies_shared_actions_to_each_origin_and_completes_blocks(
    tmp_path: Path,
    monkeypatch,
) -> None:
    app = _qapp()
    from PySide6.QtWidgets import QLabel, QPushButton

    import app.ui.pages.combined_review_dialog as dialog_module
    from app.ui.pages.combined_review_dialog import CombinedReviewSessionDialog
    from app.ui.theme import COLORS, apply_app_theme

    monkeypatch.setattr(dialog_module, "show_toast", lambda *args, **kwargs: None)
    apply_app_theme(app)
    storage, first, second = _blocks(tmp_path)
    dialog = CombinedReviewSessionDialog(
        storage,
        [first.id, second.id],
        settings_provider=lambda: {"review_cycle_enabled": True},
    )
    dialog.resize(1366, 768)
    dialog.show()
    app.processEvents()
    image = dialog.grab().toImage()
    expected_background = COLORS["background"].lower()
    assert image.pixelColor(1, 1).name().lower() == expected_background
    assert (
        image.pixelColor(dialog.width() // 2, dialog.height() - 10).name().lower()
        == expected_background
    )
    assert any(
        item.text() == "Origem: Arrays + Listas"
        for item in dialog.findChildren(QLabel)
    )
    card = dialog.session.flashcards[0]
    question = dialog.session.questions[0]

    dialog._rate_card(card, "good")
    dialog.selected_answers[dialog._question_key(question)] = "A"
    dialog._submit_answer(question, QLabel(), {}, QPushButton())
    dialog._complete()

    for block in (first, second):
        progress = storage.get_progress(block.id)
        assert progress.reviewed_flashcards[block.flashcards[0].id] == "good"
        assert progress.answered_questions[block.questions[0].id]["is_correct"] is True
        assert len(storage.list_review_schedules(block.id)) == 4
    assert storage.database_stats()["study_blocks"] == 2
