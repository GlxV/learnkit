from __future__ import annotations

from app.domain.services.review_scheduler import ReviewScheduler


def test_review_scheduler_easy_initial_review_sets_future_due_date() -> None:
    review = ReviewScheduler().next_review({}, "easy")

    assert review["status"] == "easy"
    assert review["times_reviewed"] == 1
    assert review["interval_days"] >= 4
    assert review["ease_factor"] > 2.5
    assert review["due_at"] > review["last_reviewed_at"]


def test_review_scheduler_again_keeps_card_due_and_reduces_ease() -> None:
    review = ReviewScheduler().next_review(
        {"times_reviewed": 2, "interval_days": 5, "ease_factor": 2.4},
        "again",
    )

    assert review["status"] == "again"
    assert review["times_reviewed"] == 3
    assert review["interval_days"] == 0
    assert review["ease_factor"] == 2.2
    assert review["due_at"] == review["last_reviewed_at"]
