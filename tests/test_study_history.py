from pathlib import Path

from app.core.services.block_service import BlockService
from app.core.services.module_service import ModuleService
from app.core.services.study_history_service import StudyHistoryService
from app.core.services.subject_service import SubjectService
from app.core.storage.local_storage import LocalStorage


def test_study_history_records_results_and_returns_stats(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    SubjectService(storage).create_subject("Biologia")
    ModuleService(storage).create_module("Biologia", "Prova 1")
    block = BlockService(storage).create_block("Biologia", "Prova 1", "Celulas")
    history = StudyHistoryService(storage)

    first = history.record_result(
        block_id=block.id,
        item_type="flashcard",
        item_id="card-1",
        result="correct",
        difficulty="easy",
        duration_seconds=20,
    )
    history.record_result(
        block_id=block.id,
        item_type="question",
        item_id="question-1",
        result="incorrect",
        difficulty="hard",
        duration_seconds=45,
    )

    records = history.list_records(block.id)
    stats = history.get_stats(block.id)

    assert first.block_id == block.id
    assert len(records) == 2
    assert stats.total_reviews == 2
    assert stats.correct == 1
    assert stats.incorrect == 1
    assert stats.accuracy == 0.5
    assert stats.total_duration_seconds == 65
    assert (tmp_path / "study_history.json").exists()
