from __future__ import annotations

from pathlib import Path

from app.application.query_services.study_session_query_service import StudySessionQueryService
from app.core.database import SQLiteStorage
from app.core.models.flashcard import Flashcard
from app.core.models.question import Question
from app.core.services.progress_service import ProgressService


def _create_study_block(tmp_path: Path):
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Estrutura de Dados")
    module = storage.create_module(subject.slug, "Revisao")
    block = storage.create_block(subject.slug, module.slug, "Pilhas e Filas")
    block.flashcards = [
        Flashcard("Card novo", "Resposta"),
        Flashcard("Card vencido", "Resposta"),
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
    return storage, block


def test_study_session_query_service_returns_block_context(tmp_path: Path) -> None:
    storage, block = _create_study_block(tmp_path)

    context = StudySessionQueryService(storage).block_context(block.id)

    assert context.subject.name == "Estrutura de Dados"
    assert context.module.name == "Revisao"
    assert context.block.title == "Pilhas e Filas"


def test_study_session_query_service_returns_flashcard_session(tmp_path: Path) -> None:
    storage, block = _create_study_block(tmp_path)
    ProgressService(storage).record_flashcard(block.id, block.flashcards[1].id, "again")

    session = StudySessionQueryService(storage).flashcard_session(block.id)

    assert [card.question for card in session.cards] == ["Card novo", "Card vencido"]
    assert session.progress.flashcards_total == 2
    assert session.queue[0]["card_id"] == block.flashcards[1].id
    assert session.queue[0]["state"] == "due"


def test_study_session_query_service_returns_question_session_with_filter(tmp_path: Path) -> None:
    storage, block = _create_study_block(tmp_path)
    ProgressService(storage).record_question(block.id, block.questions[0].id, "C", "A")

    session = StudySessionQueryService(storage).question_session(block.id, "wrong")

    assert [question.statement for question in session.questions] == [
        "Qual estrutura usa LIFO?",
        "Qual estrutura usa FIFO?",
    ]
    assert session.progress.questions_total == 2
    assert len(session.queue) == 1
    assert session.queue[0]["question_id"] == block.questions[0].id
    assert session.queue[0]["state"] == "wrong"


def test_record_access_starts_cycle_for_existing_block_only_when_automatic_enabled(
    tmp_path: Path,
) -> None:
    storage, block = _create_study_block(tmp_path)

    StudySessionQueryService(storage).record_access(block.id)
    assert storage.list_review_schedules(block.id) == []

    StudySessionQueryService(
        storage,
        settings_provider=lambda: {"review_cycle_enabled": True},
    ).record_access(block.id)

    assert len(storage.list_review_schedules(block.id)) == 4
