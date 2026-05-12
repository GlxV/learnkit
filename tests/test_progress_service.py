from pathlib import Path

from app.core.services.block_service import BlockService
from app.core.services.module_service import ModuleService
from app.core.services.progress_service import ProgressService
from app.core.services.subject_service import SubjectService
from app.core.storage.local_storage import LocalStorage


def _create_block(tmp_path: Path):
    storage = LocalStorage(tmp_path)
    SubjectService(storage).create_subject("Matematica", icon="Mx", color="#3B82F6")
    ModuleService(storage).create_module("Matematica", "Prova 1")
    block = BlockService(storage).create_block("Matematica", "Prova 1", "Funcoes")
    BlockService(storage).update_study_materials(
        block.id,
        "- resumo",
        [
            {"question": "q1", "answer": "a1"},
            {"question": "q2", "answer": "a2"},
        ],
        [
            {
                "statement": "p1",
                "alternatives": {"A": "a", "B": "b", "C": "c", "D": "d"},
                "correct_answer": "A",
            }
        ],
    )
    return storage, block.id


def test_progress_records_flashcards_and_questions_without_double_counting(tmp_path: Path) -> None:
    storage, block_id = _create_block(tmp_path)
    service = ProgressService(storage)

    service.record_flashcard(block_id, "card-1", "mastered")
    service.record_flashcard(block_id, "card-1", "difficult")
    service.record_question(block_id, "question-1", "A", "A")
    service.record_question(block_id, "question-1", "B", "A")

    progress = service.get_block_progress(block_id)

    assert progress.flashcards_reviewed == 1
    assert progress.flashcards_mastered == 0
    assert progress.flashcards_difficult == 1
    assert progress.questions_answered == 1
    assert progress.questions_correct == 0
    assert progress.questions_wrong == 1
    assert (tmp_path / "subjects" / "matematica" / "modules" / "prova_1" / "blocks" / "funcoes" / "progress.json").exists()


def test_progress_global_stats_use_real_saved_data(tmp_path: Path) -> None:
    storage, block_id = _create_block(tmp_path)
    service = ProgressService(storage)
    service.record_flashcard(block_id, "card-1", "mastered")
    service.record_question(block_id, "question-1", "A", "A")

    stats = service.get_global_stats()

    assert stats.total_subjects == 1
    assert stats.total_modules == 1
    assert stats.total_blocks == 1
    assert stats.total_flashcards == 2
    assert stats.total_questions == 1
    assert stats.flashcards_reviewed == 1
    assert stats.questions_answered == 1


def test_progress_records_anki_like_flashcard_ratings(tmp_path: Path) -> None:
    storage, block_id = _create_block(tmp_path)
    BlockService(storage).update_study_materials(
        block_id,
        "- resumo",
        [
            {"question": "q1", "answer": "a1"},
            {"question": "q2", "answer": "a2"},
            {"question": "q3", "answer": "a3"},
        ],
        [],
    )
    service = ProgressService(storage)

    service.record_flashcard(block_id, "card-1", "again")
    service.record_flashcard(block_id, "card-2", "good")
    service.record_flashcard(block_id, "card-3", "easy")

    progress = service.get_block_progress(block_id)

    assert progress.flashcards_reviewed == 3
    assert progress.flashcards_again == 1
    assert progress.flashcards_good == 1
    assert progress.flashcards_easy == 1
    assert progress.flashcards_mastered == 1
    assert progress.flashcards_difficult == 1
