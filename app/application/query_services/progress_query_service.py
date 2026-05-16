from __future__ import annotations

from app.application.dto.progress import (
    FlashcardQueueItemDTO,
    QuestionQueueItemDTO,
    ReviewDashboardDTO,
)
from app.core.services.progress_reader import ProgressReader


class ProgressQueryService(ProgressReader):
    """Application-facing progress read service.

    The implementation lives in the legacy core reader so old core services can
    preserve their public API without depending on the application layer.
    """

    def flashcard_queue_dto(
        self,
        block_id: str,
        include_future: bool = True,
    ) -> list[FlashcardQueueItemDTO]:
        return [
            FlashcardQueueItemDTO.from_mapping(item)
            for item in self.flashcard_queue(block_id, include_future)
        ]

    def question_queue_dto(
        self,
        block_id: str,
        filter_mode: str = "all",
    ) -> list[QuestionQueueItemDTO]:
        return [
            QuestionQueueItemDTO.from_mapping(item)
            for item in self.question_queue(block_id, filter_mode)
        ]

    def review_dashboard_dto(self, subject_ref: str | None = None) -> ReviewDashboardDTO:
        return ReviewDashboardDTO.from_mapping(self.review_dashboard(subject_ref))
