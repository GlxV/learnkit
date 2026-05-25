from datetime import datetime, timedelta, timezone
import pytest

from app.domain.services.block_review_cycle_scheduler import BlockReviewCycleScheduler


def test_review_cycle_scheduler_builds_standard_intervals_in_utc() -> None:
    studied_at = datetime(2026, 5, 19, 23, 0, tzinfo=timezone.utc)

    schedules = BlockReviewCycleScheduler().create_schedules(
        study_block_id="block-1",
        subject_id="subject-1",
        module_id="module-1",
        studied_at=studied_at,
    )

    dates = {item.review_step: datetime.fromisoformat(item.scheduled_at) for item in schedules}
    assert dates["1h"] == studied_at + timedelta(hours=1)
    assert dates["24h"] == studied_at + timedelta(hours=24)
    assert dates["7d"] == studied_at + timedelta(days=7)
    assert dates["30d"] == studied_at + timedelta(days=30)


def test_review_cycle_scheduler_uses_preferred_local_time_only_for_daily_steps() -> None:
    sao_paulo = timezone(timedelta(hours=-3))
    studied_local = datetime(2026, 5, 19, 20, 0, tzinfo=sao_paulo)

    schedules = BlockReviewCycleScheduler().create_schedules(
        study_block_id="block-1",
        subject_id="subject-1",
        module_id="module-1",
        studied_at=studied_local,
        settings={"preferred_review_time": "20:00"},
        local_timezone=sao_paulo,
    )

    dates = {
        item.review_step: datetime.fromisoformat(item.scheduled_at).astimezone(sao_paulo)
        for item in schedules
    }
    assert dates["1h"] == datetime(2026, 5, 19, 21, 0, tzinfo=sao_paulo)
    assert dates["24h"] == datetime(2026, 5, 20, 20, 0, tzinfo=sao_paulo)
    assert dates["7d"] == datetime(2026, 5, 26, 20, 0, tzinfo=sao_paulo)
    assert dates["30d"] == datetime(2026, 6, 18, 20, 0, tzinfo=sao_paulo)


def test_review_cycle_scheduler_generates_only_enabled_steps() -> None:
    schedules = BlockReviewCycleScheduler().create_schedules(
        study_block_id="block-1",
        subject_id="subject-1",
        module_id="module-1",
        studied_at=datetime(2026, 5, 24, tzinfo=timezone.utc),
        settings={
            "review_step_1h_enabled": False,
            "review_step_24h_enabled": False,
            "review_step_7d_enabled": True,
            "review_step_30d_enabled": False,
        },
    )

    assert [item.review_step for item in schedules] == ["7d"]


def test_review_cycle_scheduler_requires_at_least_one_enabled_step() -> None:
    with pytest.raises(ValueError, match="pelo menos uma etapa"):
        BlockReviewCycleScheduler().create_schedules(
            study_block_id="block-1",
            subject_id="subject-1",
            module_id="module-1",
            studied_at=datetime(2026, 5, 24, tzinfo=timezone.utc),
            settings={
                "review_step_1h_enabled": False,
                "review_step_24h_enabled": False,
                "review_step_7d_enabled": False,
                "review_step_30d_enabled": False,
            },
        )
