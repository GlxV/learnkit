from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.application.query_services.review_cycle_query_service import ReviewCycleQueryService
from app.application.use_cases.manage_review_cycle import ManageReviewCycleUseCase
from app.core.database import SQLiteStorage
from app.core.models.flashcard import Flashcard
from app.core.models.question import Question
from app.core.models.review_schedule import ReviewSchedule
from app.core.models.summary import Summary


def _block(storage: SQLiteStorage, title: str = "BFS e DFS"):
    subject = storage.create_subject(f"Estrutura de Dados {title}")
    module = storage.create_module(subject.slug, "Grafos")
    block = storage.create_block(subject.slug, module.slug, title)
    return subject, module, block


def test_manual_activation_works_with_global_creation_disabled_and_is_idempotent(
    tmp_path: Path,
) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    _subject, _module, block = _block(storage)
    use_case = ManageReviewCycleUseCase(storage)

    first = use_case.activate_cycle(
        block.id,
        studied_at=datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
        settings={"review_cycle_enabled": False},
        automatic=False,
    )
    second = use_case.activate_cycle(
        block.id,
        studied_at=datetime(2026, 5, 25, 12, 0, tzinfo=timezone.utc),
        settings={"review_cycle_enabled": False},
        automatic=False,
    )

    assert first.created is True
    assert len(first.schedules) == 4
    assert second.created is False
    assert len(storage.list_review_schedules(block.id)) == 4


def test_automatic_activation_requires_global_setting(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    _subject, _module, block = _block(storage)
    use_case = ManageReviewCycleUseCase(storage)

    disabled = use_case.activate_cycle(
        block.id,
        studied_at=datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
        settings={"review_cycle_enabled": False},
        automatic=True,
    )
    enabled = use_case.activate_cycle(
        block.id,
        studied_at=datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
        settings={"review_cycle_enabled": True},
        automatic=True,
    )

    assert disabled.created is False
    assert disabled.schedules == []
    assert enabled.created is True
    assert len(enabled.schedules) == 4


def test_automatic_activation_with_no_enabled_step_does_not_block_study_flow(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    _subject, _module, block = _block(storage)

    result = ManageReviewCycleUseCase(storage).activate_cycle(
        block.id,
        studied_at=datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
        settings={
            "review_cycle_enabled": True,
            "review_step_1h_enabled": False,
            "review_step_24h_enabled": False,
            "review_step_7d_enabled": False,
            "review_step_30d_enabled": False,
        },
        automatic=True,
    )

    assert result.created is False
    assert result.reason == "no_enabled_steps"
    assert storage.list_review_schedules(block.id) == []


def test_review_action_marks_done_or_skipped_without_affecting_next_steps(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    _subject, _module, block = _block(storage)
    schedules = ManageReviewCycleUseCase(storage).activate_cycle(
        block.id,
        studied_at=datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
        automatic=False,
    ).schedules

    done = ManageReviewCycleUseCase(storage).complete_review(
        schedules[0].id,
        completed_at=datetime(2026, 5, 24, 13, 5, tzinfo=timezone.utc),
    )
    skipped = ManageReviewCycleUseCase(storage).skip_review(
        schedules[1].id,
        completed_at=datetime(2026, 5, 25, 12, 5, tzinfo=timezone.utc),
    )

    assert done.status == "done"
    assert skipped.status == "skipped"
    assert [item.status for item in storage.list_review_schedules(block.id)] == [
        "done",
        "skipped",
        "pending",
        "pending",
    ]


def test_review_queue_groups_pending_items_by_local_day(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject, module, block = _block(storage)
    now = datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc)
    storage.create_review_schedules(
        [
            ReviewSchedule(block.id, subject.id, module.id, "1h", (now - timedelta(days=1)).isoformat()),
            ReviewSchedule(block.id, subject.id, module.id, "24h", (now - timedelta(hours=1)).isoformat()),
            ReviewSchedule(block.id, subject.id, module.id, "7d", (now + timedelta(days=2)).isoformat()),
        ]
    )

    queue = ReviewCycleQueryService(storage).queue(now=now, local_timezone=timezone.utc)

    assert [item.review_step for item in queue.overdue] == ["1h"]
    assert [item.review_step for item in queue.today] == ["24h"]
    assert [item.review_step for item in queue.upcoming] == ["7d"]
    assert queue.next_scheduled_at == (now - timedelta(days=1)).isoformat()


@pytest.mark.parametrize("included", ["summary", "flashcards", "questions"])
def test_review_session_supports_partial_block_content(tmp_path: Path, included: str) -> None:
    storage = SQLiteStorage(tmp_path / f"{included}.db", migrate_json=False)
    subject, module, block = _block(storage, included)
    if included == "summary":
        block.summary = Summary("Um resumo curto para relembrar.")
    elif included == "flashcards":
        block.flashcards = [Flashcard("Frente?", "Verso.")]
    else:
        block.questions = [
            Question("Pergunta?", {"A": "Sim", "B": "Nao", "C": "-", "D": "-"}, "A")
        ]
    storage.save_block(subject, module, block)
    schedule = ManageReviewCycleUseCase(storage).activate_cycle(
        block.id,
        studied_at=datetime(2026, 5, 24, tzinfo=timezone.utc),
        settings={
            "review_step_1h_enabled": True,
            "review_step_24h_enabled": False,
            "review_step_7d_enabled": False,
            "review_step_30d_enabled": False,
        },
    ).schedules[0]

    session = ReviewCycleQueryService(storage).session(schedule.id)

    assert bool(session.summary_text) is (included == "summary")
    assert bool(session.flashcards) is (included == "flashcards")
    assert bool(session.questions) is (included == "questions")
