from __future__ import annotations

from pathlib import Path

from app.application.query_services.progress_query_service import ProgressQueryService
from app.core.database import SQLiteStorage
from app.core.models.flashcard import Flashcard
from app.core.models.question import Question
from app.core.services.progress_service import ProgressService


def _create_progress_fixture(tmp_path: Path):
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Estrutura de Dados")
    module = storage.create_module(subject.slug, "Revisao")
    block = storage.create_block(subject.slug, module.slug, "Pilhas e Filas")
    block.flashcards = [
        Flashcard("Card novo", "Resposta"),
        Flashcard("Card vencido", "Resposta"),
        Flashcard("Card futuro", "Resposta"),
    ]
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
    ]
    storage.save_block(subject, module, block)
    progress = ProgressService(storage)
    progress.record_flashcard(block.id, block.flashcards[1].id, "again")
    progress.record_flashcard(block.id, block.flashcards[2].id, "easy")
    progress.record_question(block.id, block.questions[0].id, "C", "A")
    return storage, block


def test_progress_query_service_returns_block_progress_and_queues(tmp_path: Path) -> None:
    storage, block = _create_progress_fixture(tmp_path)
    query = ProgressQueryService(storage)

    progress = query.block_progress(block.id)
    flashcards = query.flashcard_queue(block.id)
    questions = query.question_queue(block.id, "wrong")

    assert progress.flashcards_total == 3
    assert progress.questions_total == 2
    assert [item["state"] for item in flashcards] == ["due", "new", "future"]
    assert len(questions) == 1
    assert questions[0]["question_id"] == block.questions[0].id


def test_progress_query_service_returns_global_stats_and_dashboard(tmp_path: Path) -> None:
    storage, block = _create_progress_fixture(tmp_path)
    query = ProgressQueryService(storage)

    stats = query.global_stats()
    dashboard = query.review_dashboard()

    assert stats.total_subjects == 1
    assert stats.total_flashcards == 3
    assert stats.flashcards_reviewed == 2
    assert dashboard["summary"]["due_flashcards"] == 1
    assert dashboard["summary"]["future_flashcards"] == 1
    assert dashboard["summary"]["wrong_questions"] == 1
    assert dashboard["blocks"][0]["block_id"] == block.id


def test_progress_query_service_exposes_typed_dtos(tmp_path: Path) -> None:
    storage, block = _create_progress_fixture(tmp_path)
    query = ProgressQueryService(storage)

    flashcards = query.flashcard_queue_dto(block.id)
    questions = query.question_queue_dto(block.id, "wrong")
    dashboard = query.review_dashboard_dto()

    assert flashcards[0].card_id == block.flashcards[1].id
    assert flashcards[0].state == "due"
    assert questions[0].question_id == block.questions[0].id
    assert dashboard.summary.due_flashcards == 1
    assert dashboard.blocks[0].block_id == block.id
    assert dashboard.to_dict()["summary"]["wrong_questions"] == 1


def test_progress_service_does_not_depend_on_application_layer() -> None:
    source = Path("app/core/services/progress_service.py").read_text(encoding="utf-8")

    assert "app.application" not in source
