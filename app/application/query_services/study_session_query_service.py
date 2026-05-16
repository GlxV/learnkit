from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.query_services.progress_query_service import ProgressQueryService
from app.core.models.flashcard import Flashcard
from app.core.models.module import Module
from app.core.models.progress import StudyProgress
from app.core.models.question import Question
from app.core.models.study_block import StudyBlock
from app.core.models.subject import Subject
from app.core.storage.local_storage import LocalStorage


@dataclass(slots=True)
class StudyBlockContextDTO:
    subject: Subject
    module: Module
    block: StudyBlock


@dataclass(slots=True)
class FlashcardSessionDTO:
    block: StudyBlock
    cards: list[Flashcard]
    progress: StudyProgress
    queue: list[dict[str, Any]]


@dataclass(slots=True)
class QuestionSessionDTO:
    block: StudyBlock
    questions: list[Question]
    progress: StudyProgress
    queue: list[dict[str, Any]]


class StudySessionQueryService:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage
        self.progress_query_service = ProgressQueryService(storage)

    def block_context(self, block_id: str) -> StudyBlockContextDTO:
        subject, module, block = self.storage.get_block_by_id(block_id)
        return StudyBlockContextDTO(subject=subject, module=module, block=block)

    def flashcard_session(self, block_id: str, include_future: bool = True) -> FlashcardSessionDTO:
        _, _, block = self.storage.get_block_by_id(block_id)
        return FlashcardSessionDTO(
            block=block,
            cards=block.flashcards,
            progress=self.progress_query_service.block_progress(block_id),
            queue=self.progress_query_service.flashcard_queue(block_id, include_future=include_future),
        )

    def question_session(self, block_id: str, filter_mode: str = "all") -> QuestionSessionDTO:
        _, _, block = self.storage.get_block_by_id(block_id)
        return QuestionSessionDTO(
            block=block,
            questions=block.questions,
            progress=self.progress_query_service.block_progress(block_id),
            queue=self.progress_query_service.question_queue(block_id, filter_mode),
        )

    def record_access(self, block_id: str, duration_seconds: int = 0) -> StudyProgress:
        from app.core.services.progress_service import ProgressService

        return ProgressService(self.storage).record_access(block_id, duration_seconds)
