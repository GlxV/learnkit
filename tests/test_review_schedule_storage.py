from datetime import datetime, timezone
from pathlib import Path

from app.core.database import SQLiteStorage
from app.domain.services.block_review_cycle_scheduler import BlockReviewCycleScheduler


def _create_block(storage: SQLiteStorage):
    subject = storage.create_subject("Estrutura de Dados")
    module = storage.create_module(subject.slug, "Grafos")
    block = storage.create_block(subject.slug, module.slug, "BFS e DFS")
    return subject, module, block


def test_sqlite_persists_review_cycle_without_duplicate_steps(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject, module, block = _create_block(storage)
    schedules = BlockReviewCycleScheduler().create_schedules(
        study_block_id=block.id,
        subject_id=subject.id,
        module_id=module.id,
        studied_at=datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
    )

    storage.create_review_schedules(schedules)
    storage.create_review_schedules(schedules)

    stored = storage.list_review_schedules(block.id)
    assert [item.review_step for item in stored] == ["1h", "24h", "7d", "30d"]
    assert all(item.status == "pending" for item in stored)


def test_sqlite_updates_review_status_and_preserves_other_steps(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject, module, block = _create_block(storage)
    storage.create_review_schedules(
        BlockReviewCycleScheduler().create_schedules(
            study_block_id=block.id,
            subject_id=subject.id,
            module_id=module.id,
            studied_at=datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
        )
    )
    first = storage.list_review_schedules(block.id)[0]

    updated = storage.update_review_schedule_status(
        first.id,
        "done",
        completed_at="2026-05-24T13:30:00+00:00",
    )

    assert updated.status == "done"
    assert updated.completed_at == "2026-05-24T13:30:00+00:00"
    assert len(storage.list_review_schedules(block.id)) == 4


def test_deleting_a_block_removes_its_review_cycle(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject, module, block = _create_block(storage)
    storage.create_review_schedules(
        BlockReviewCycleScheduler().create_schedules(
            study_block_id=block.id,
            subject_id=subject.id,
            module_id=module.id,
            studied_at=datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
        )
    )

    storage.delete_block(subject.slug, module.slug, block.slug)

    assert storage.list_review_schedules(block.id) == []
