from pathlib import Path

from app.core.database import SQLiteStorage
from app.core.models.flashcard import Flashcard
from app.core.models.question import Question
from app.core.services.progress_service import ProgressService


def _create_dashboard_data(tmp_path: Path):
    storage = SQLiteStorage(tmp_path / "learnkit.db")
    subject = storage.create_subject("Estrutura de Dados")
    module = storage.create_module(subject.slug, "Revisão")
    block = storage.create_block(subject.slug, module.slug, "Pilhas e Filas")
    block.flashcards = [
        Flashcard("Novo card", "Resposta"),
        Flashcard("Card vencido", "Resposta"),
        Flashcard("Card futuro", "Resposta"),
    ]
    block.questions = [
        Question(
            statement="Qual estrutura usa LIFO?",
            alternatives={"A": "Fila", "B": "Pilha", "C": "Árvore", "D": "Grafo"},
            correct_answer="B",
        ),
        Question(
            statement="Qual estrutura usa FIFO?",
            alternatives={"A": "Pilha", "B": "Lista", "C": "Fila", "D": "Hash"},
            correct_answer="C",
        ),
        Question(
            statement="Qual estrutura usa nós?",
            alternatives={"A": "Árvore", "B": "SELECT", "C": "DROP", "D": "WHERE"},
            correct_answer="A",
        ),
    ]
    storage.save_block(subject, module, block)
    service = ProgressService(storage)
    service.record_flashcard(block.id, block.flashcards[1].id, "again")
    service.record_flashcard(block.id, block.flashcards[2].id, "easy")
    service.record_question(block.id, block.questions[0].id, "B", "B")
    service.record_question(block.id, block.questions[1].id, "A", "C")
    return storage, block


def test_review_dashboard_counts_pending_work_and_activity(tmp_path: Path) -> None:
    storage, block = _create_dashboard_data(tmp_path)

    dashboard = ProgressService(storage).get_review_dashboard()

    assert dashboard["summary"]["due_flashcards"] == 1
    assert dashboard["summary"]["new_flashcards"] == 1
    assert dashboard["summary"]["future_flashcards"] == 1
    assert dashboard["summary"]["wrong_questions"] == 1
    assert dashboard["summary"]["correct_questions"] == 1
    assert dashboard["summary"]["unanswered_questions"] == 1
    assert dashboard["summary"]["pending_reviews"] == 4
    assert dashboard["blocks"][0]["block_id"] == block.id
    assert dashboard["blocks"][0]["pending_reviews"] == 4
    assert len(dashboard["activity"]) >= 4


def test_review_dashboard_can_filter_by_subject(tmp_path: Path) -> None:
    storage, _block = _create_dashboard_data(tmp_path)
    other = storage.create_subject("História")
    module = storage.create_module(other.slug, "Prova")
    block = storage.create_block(other.slug, module.slug, "Império")
    block.flashcards = [Flashcard("Card de História", "Resposta")]
    storage.save_block(other, module, block)

    dashboard = ProgressService(storage).get_review_dashboard("História")

    assert dashboard["summary"]["new_flashcards"] == 1
    assert dashboard["summary"]["due_flashcards"] == 0
    assert dashboard["blocks"][0]["subject_name"] == "História"
