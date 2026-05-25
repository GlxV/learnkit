from __future__ import annotations

from datetime import datetime, timedelta, timezone, tzinfo

from app.application.dto.review_cycle import (
    ReviewBlockCycleDTO,
    ReviewQueueDTO,
    ReviewQueueItemDTO,
    ReviewSessionDTO,
)
from app.application.query_services.progress_query_service import ProgressQueryService
from app.core.models.review_schedule import ReviewSchedule
from app.core.storage.local_storage import LocalStorage


class ReviewCycleQueryService:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage
        self.progress_query_service = ProgressQueryService(storage)

    def block_cycle(self, block_id: str) -> ReviewBlockCycleDTO:
        schedules = self._for_block(block_id)
        pending = [item for item in schedules if item.status == "pending"]
        return ReviewBlockCycleDTO(
            block_id=block_id,
            schedules=schedules,
            pending=len(pending),
            done=len([item for item in schedules if item.status == "done"]),
            skipped=len([item for item in schedules if item.status == "skipped"]),
            next_pending=min(pending, key=lambda item: item.scheduled_at) if pending else None,
        )

    def queue(
        self,
        *,
        now: datetime | None = None,
        local_timezone: tzinfo | None = None,
        subject_name: str | None = None,
    ) -> ReviewQueueDTO:
        timezone_for_display = (
            local_timezone or datetime.now().astimezone().tzinfo or timezone.utc
        )
        now_local = self._aware(now or datetime.now(timezone.utc)).astimezone(
            timezone_for_display
        )
        day_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        next_day = day_start + timedelta(days=1)
        items = [self._queue_item(item) for item in self._pending()]
        if subject_name:
            items = [item for item in items if item.subject_name == subject_name]
        overdue: list[ReviewQueueItemDTO] = []
        today: list[ReviewQueueItemDTO] = []
        upcoming: list[ReviewQueueItemDTO] = []
        for item in items:
            scheduled_local = self._aware(datetime.fromisoformat(item.scheduled_at)).astimezone(
                timezone_for_display
            )
            if scheduled_local < day_start:
                overdue.append(item)
            elif scheduled_local < next_day:
                today.append(item)
            else:
                upcoming.append(item)
        return ReviewQueueDTO(
            overdue=overdue,
            today=today,
            upcoming=upcoming,
            next_scheduled_at=items[0].scheduled_at if items else "",
        )

    def session(self, schedule_id: str) -> ReviewSessionDTO:
        schedule = self.storage.get_review_schedule(schedule_id)  # type: ignore[attr-defined]
        _subject, _module, block = self.storage.get_block_by_id(schedule.study_block_id)
        progress = self.progress_query_service.block_progress(block.id)
        difficult = {
            card_id
            for card_id, review in progress.flashcard_reviews.items()
            if isinstance(review, dict)
            and str(review.get("status", "")) in {"again", "hard", "difficult"}
        }
        cards = sorted(block.flashcards, key=lambda card: (card.id not in difficult, card.id))
        question_limit = {"1h": 1, "24h": 2, "7d": 2, "30d": 3}.get(schedule.review_step, 1)
        return ReviewSessionDTO(
            review=self._queue_item(schedule),
            summary_text=block.summary.content if block.summary else "",
            flashcards=cards[:3],
            questions=block.questions[:question_limit],
            progress=progress,
        )

    def _queue_item(self, schedule: ReviewSchedule) -> ReviewQueueItemDTO:
        subject, module, block = self.storage.get_block_by_id(schedule.study_block_id)
        return ReviewQueueItemDTO(
            schedule_id=schedule.id,
            block_id=block.id,
            block_title=block.title,
            subject_name=subject.name,
            module_name=module.name,
            review_step=schedule.review_step,
            scheduled_at=schedule.scheduled_at,
            status=schedule.status,
            completed_at=schedule.completed_at,
        )

    def _pending(self) -> list[ReviewSchedule]:
        if not hasattr(self.storage, "list_pending_review_schedules"):
            return []
        return self.storage.list_pending_review_schedules()  # type: ignore[attr-defined]

    def _for_block(self, block_id: str) -> list[ReviewSchedule]:
        if not hasattr(self.storage, "list_review_schedules"):
            return []
        return self.storage.list_review_schedules(block_id)  # type: ignore[attr-defined]

    def _aware(self, value: datetime) -> datetime:
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
