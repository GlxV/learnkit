from __future__ import annotations

import os
import sys
from pathlib import Path


def _qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def _storage_with_questions(tmp_path: Path):
    from app.core.database import SQLiteStorage
    from app.core.models.question import Question

    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Estrutura de Dados")
    module = storage.create_module(subject.slug, "Revisao")
    block = storage.create_block(subject.slug, module.slug, "Pilhas e Filas")
    block.questions = [
        Question(
            statement="Qual estrutura usa LIFO?",
            alternatives={"A": "Pilha", "B": "Fila", "C": "Grafo", "D": "Hash"},
            correct_answer="A",
        ),
        Question(
            statement="Qual estrutura usa FIFO?",
            alternatives={"A": "Pilha", "B": "Fila", "C": "Grafo", "D": "Hash"},
            correct_answer="B",
        ),
        Question(
            statement="Qual estrutura usa indice?",
            alternatives={"A": "Fila", "B": "Pilha", "C": "Array", "D": "Grafo"},
            correct_answer="C",
        ),
    ]
    storage.save_block(subject, module, block)
    return storage, block


def test_questions_page_advances_to_next_question_after_answer(tmp_path, monkeypatch) -> None:
    _qapp()

    from app.application.query_services.ui_data_provider import UIDataProvider
    import app.ui.pages.questions_page as questions_module
    from app.ui.pages.questions_page import QuestionsPage

    monkeypatch.setattr(questions_module, "show_toast", lambda *args, **kwargs: None)
    storage, block = _storage_with_questions(tmp_path)
    page = QuestionsPage(UIDataProvider(storage), storage)
    page.select_block_by_id(block.id)

    first_id = block.questions[0].id
    second_id = block.questions[1].id

    assert page.question_queue[page.current_index]["question_id"] == first_id

    page._select_answer("A")
    page._answer()

    assert page.question_queue[page.current_index]["question_id"] == first_id
    assert page.answered is True

    page._next()

    assert page.question_queue[page.current_index]["question_id"] == second_id
    assert page.answered is False

    page._select_answer("B")
    page._answer()

    assert page.question_queue[page.current_index]["question_id"] == second_id
    assert page.answered is True
