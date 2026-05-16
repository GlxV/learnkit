from __future__ import annotations

from app.core.models.progress import StudyProgress
from app.core.services.progress_service import ProgressService
from app.core.storage.local_storage import LocalStorage


class AnswerQuestionUseCase:
    def __init__(self, storage: LocalStorage) -> None:
        self.progress_service = ProgressService(storage)

    def execute(
        self,
        block_id: str,
        question_id: str,
        selected_answer: str,
        correct_answer: str,
    ) -> StudyProgress:
        return self.progress_service.record_question(
            block_id,
            question_id,
            selected_answer,
            correct_answer,
        )
