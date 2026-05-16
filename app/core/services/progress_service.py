from __future__ import annotations

import json
from typing import Any

from app.core.models.base import utc_now
from app.core.models.progress import AggregateProgress, StudyProgress
from app.core.models.study_block import StudyBlock
from app.core.services.progress_reader import ProgressReader
from app.core.storage.local_storage import LocalStorage
from app.domain.services.review_scheduler import ReviewScheduler


class ProgressService:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage
        self.scheduler = ReviewScheduler()
        self.progress_reader = ProgressReader(storage)

    def get_block_progress(self, block_id: str) -> StudyProgress:
        return self.progress_reader.block_progress(block_id)

    def save_block_progress(self, block_id: str, progress: StudyProgress) -> StudyProgress:
        subject, module, block = self.storage.get_block_by_id(block_id)
        progress = self.progress_reader.with_totals(progress, block)
        progress.updated_at = utc_now()
        if hasattr(self.storage, "save_progress"):
            return self.storage.save_progress(block_id, progress)
        path = self.storage.block_path(subject.slug, module.slug, block.slug) / "progress.json"
        path.write_text(
            json.dumps(progress.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return progress

    def record_access(self, block_id: str, duration_seconds: int = 0) -> StudyProgress:
        progress = self.get_block_progress(block_id)
        progress.last_accessed_at = utc_now()
        progress.study_time_seconds += max(0, duration_seconds)
        return self.save_block_progress(block_id, progress)

    def record_flashcard(self, block_id: str, flashcard_id: str, status: str) -> StudyProgress:
        normalized = {
            "again": "again",
            "hard": "hard",
            "good": "good",
            "easy": "easy",
            "mastered": "easy",
            "difficult": "hard",
            "skipped": "skipped",
        }.get(status)
        if normalized is None:
            raise ValueError("Status de flashcard invalido.")
        _, _, block = self.storage.get_block_by_id(block_id)
        flashcard_id = self._resolve_flashcard_id(block, flashcard_id)
        progress = self.get_block_progress(block_id)
        progress.reviewed_flashcards[flashcard_id] = normalized
        progress.flashcard_reviews[flashcard_id] = self.scheduler.next_review(
            progress.flashcard_reviews.get(flashcard_id, {}),
            normalized,
        )
        progress.last_accessed_at = utc_now()
        return self.save_block_progress(block_id, progress)

    def get_flashcard_queue(
        self,
        block_id: str,
        include_future: bool = True,
    ) -> list[dict[str, Any]]:
        return self.progress_reader.flashcard_queue(block_id, include_future)

    def record_question(
        self,
        block_id: str,
        question_id: str,
        selected_answer: str,
        correct_answer: str,
    ) -> StudyProgress:
        selected = selected_answer.strip().upper()
        correct = correct_answer.strip().upper()
        _, _, block = self.storage.get_block_by_id(block_id)
        question_id = self._resolve_question_id(block, question_id)
        progress = self.get_block_progress(block_id)
        attempt = {
            "selected_answer": selected,
            "correct_answer": correct,
            "is_correct": selected == correct,
            "answered_at": utc_now(),
        }
        progress.answered_questions[question_id] = attempt
        progress.question_attempts.setdefault(question_id, []).append(attempt)
        progress.last_accessed_at = utc_now()
        return self.save_block_progress(block_id, progress)

    def get_question_queue(self, block_id: str, filter_mode: str = "all") -> list[dict[str, Any]]:
        return self.progress_reader.question_queue(block_id, filter_mode)

    def get_global_stats(self) -> AggregateProgress:
        return self.progress_reader.global_stats()

    def get_review_dashboard(self, subject_ref: str | None = None) -> dict[str, Any]:
        return self.progress_reader.review_dashboard(subject_ref)

    def _resolve_flashcard_id(self, block: StudyBlock, flashcard_id: str) -> str:
        if flashcard_id in {card.id for card in block.flashcards}:
            return flashcard_id
        if flashcard_id.startswith("card-"):
            try:
                index = int(flashcard_id.removeprefix("card-")) - 1
            except ValueError:
                return flashcard_id
            if 0 <= index < len(block.flashcards):
                return block.flashcards[index].id
        return flashcard_id

    def _resolve_question_id(self, block: StudyBlock, question_id: str) -> str:
        if question_id in {question.id for question in block.questions}:
            return question_id
        if question_id.startswith("question-"):
            try:
                index = int(question_id.removeprefix("question-")) - 1
            except ValueError:
                return question_id
            if 0 <= index < len(block.questions):
                return block.questions[index].id
        return question_id
