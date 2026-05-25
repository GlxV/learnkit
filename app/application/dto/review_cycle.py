from __future__ import annotations

from dataclasses import dataclass, field

from app.core.models.flashcard import Flashcard
from app.core.models.progress import StudyProgress
from app.core.models.question import Question
from app.core.models.review_schedule import ReviewSchedule


@dataclass(frozen=True, slots=True)
class ReviewCycleActivationDTO:
    created: bool
    schedules: list[ReviewSchedule] = field(default_factory=list)
    reason: str = ""


@dataclass(frozen=True, slots=True)
class ReviewQueueItemDTO:
    schedule_id: str
    block_id: str
    block_title: str
    subject_name: str
    module_name: str
    review_step: str
    scheduled_at: str
    status: str
    completed_at: str | None = None


@dataclass(frozen=True, slots=True)
class ReviewQueueDTO:
    overdue: list[ReviewQueueItemDTO] = field(default_factory=list)
    today: list[ReviewQueueItemDTO] = field(default_factory=list)
    upcoming: list[ReviewQueueItemDTO] = field(default_factory=list)
    next_scheduled_at: str = ""

    @property
    def overdue_count(self) -> int:
        return len(self.overdue)

    @property
    def today_count(self) -> int:
        return len(self.today)

    @property
    def pending_count(self) -> int:
        return len(self.overdue) + len(self.today) + len(self.upcoming)


@dataclass(frozen=True, slots=True)
class ReviewBlockCycleDTO:
    block_id: str
    schedules: list[ReviewSchedule] = field(default_factory=list)
    pending: int = 0
    done: int = 0
    skipped: int = 0
    next_pending: ReviewSchedule | None = None

    @property
    def total(self) -> int:
        return len(self.schedules)


@dataclass(slots=True)
class ReviewSessionDTO:
    review: ReviewQueueItemDTO
    summary_text: str = ""
    flashcards: list[Flashcard] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)
    progress: StudyProgress = field(default_factory=StudyProgress)
