from pathlib import Path

from app.core.database import SQLiteStorage
from app.core.models.question import Question
from app.core.services.progress_service import ProgressService


def _create_block_with_questions(tmp_path: Path):
    storage = SQLiteStorage(tmp_path / "learnkit.db")
    subject = storage.create_subject("Banco de Dados")
    module = storage.create_module(subject.slug, "Prova")
    block = storage.create_block(subject.slug, module.slug, "SQL")
    block.questions = [
        Question(
            statement="Qual comando consulta dados?",
            alternatives={"A": "SELECT", "B": "DROP", "C": "DELETE", "D": "ALTER"},
            correct_answer="A",
        ),
        Question(
            statement="Qual comando apaga tabela?",
            alternatives={"A": "SELECT", "B": "DROP", "C": "JOIN", "D": "WHERE"},
            correct_answer="B",
        ),
        Question(
            statement="Qual cláusula filtra linhas?",
            alternatives={"A": "FROM", "B": "JOIN", "C": "WHERE", "D": "ORDER"},
            correct_answer="C",
        ),
    ]
    storage.save_block(subject, module, block)
    return storage, block


def test_question_attempt_history_keeps_all_attempts_without_double_counting(tmp_path: Path) -> None:
    storage, block = _create_block_with_questions(tmp_path)
    service = ProgressService(storage)
    question = block.questions[0]

    service.record_question(block.id, question.id, "B", question.correct_answer)
    progress = service.record_question(block.id, question.id, "A", question.correct_answer)

    attempts = progress.question_attempts[question.id]

    assert progress.questions_answered == 1
    assert progress.questions_correct == 1
    assert progress.questions_wrong == 0
    assert len(attempts) == 2
    assert attempts[0]["is_correct"] is False
    assert attempts[1]["is_correct"] is True


def test_question_attempt_history_persists_in_sqlite(tmp_path: Path) -> None:
    storage, block = _create_block_with_questions(tmp_path)
    service = ProgressService(storage)
    question = block.questions[1]

    service.record_question(block.id, question.id, "A", question.correct_answer)
    reopened = SQLiteStorage(tmp_path / "learnkit.db")
    progress = ProgressService(reopened).get_block_progress(block.id)

    assert progress.answered_questions[question.id]["selected_answer"] == "A"
    assert progress.question_attempts[question.id][0]["selected_answer"] == "A"
    assert progress.questions_wrong == 1


def test_question_queue_filters_unanswered_wrong_and_correct(tmp_path: Path) -> None:
    storage, block = _create_block_with_questions(tmp_path)
    service = ProgressService(storage)
    correct_question, wrong_question, unanswered_question = block.questions

    service.record_question(block.id, correct_question.id, "A", correct_question.correct_answer)
    service.record_question(block.id, wrong_question.id, "A", wrong_question.correct_answer)

    assert [item["question_id"] for item in service.get_question_queue(block.id, "correct")] == [correct_question.id]
    assert [item["question_id"] for item in service.get_question_queue(block.id, "wrong")] == [wrong_question.id]
    assert [item["question_id"] for item in service.get_question_queue(block.id, "unanswered")] == [unanswered_question.id]
    assert [item["state"] for item in service.get_question_queue(block.id, "all")] == [
        "unanswered",
        "wrong",
        "correct",
    ]
