from __future__ import annotations

from app.core.models.progress import StudyProgress
from app.core.services.progress_service import ProgressService
from app.core.storage.local_storage import LocalStorage


class ReviewFlashcardUseCase:
    def __init__(self, storage: LocalStorage) -> None:
        self.progress_service = ProgressService(storage)

    def execute(self, block_id: str, flashcard_id: str, status: str) -> StudyProgress:
        return self.progress_service.record_flashcard(block_id, flashcard_id, status)
