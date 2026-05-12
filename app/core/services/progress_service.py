from __future__ import annotations

import json

from app.core.models.base import utc_now
from app.core.models.progress import AggregateProgress, StudyProgress
from app.core.models.study_block import StudyBlock
from app.core.storage.local_storage import LocalStorage


class ProgressService:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage

    def get_block_progress(self, block_id: str) -> StudyProgress:
        subject, module, block = self.storage.get_block_by_id(block_id)
        path = self.storage.block_path(subject.slug, module.slug, block.slug) / "progress.json"
        progress = StudyProgress.from_dict(
            json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        )
        return self._with_totals(progress, block)

    def save_block_progress(self, block_id: str, progress: StudyProgress) -> StudyProgress:
        subject, module, block = self.storage.get_block_by_id(block_id)
        progress = self._with_totals(progress, block)
        progress.updated_at = utc_now()
        path = self.storage.block_path(subject.slug, module.slug, block.slug) / "progress.json"
        path.write_text(json.dumps(progress.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
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
        progress = self.get_block_progress(block_id)
        progress.reviewed_flashcards[flashcard_id] = normalized
        progress.last_accessed_at = utc_now()
        return self.save_block_progress(block_id, progress)

    def record_question(
        self,
        block_id: str,
        question_id: str,
        selected_answer: str,
        correct_answer: str,
    ) -> StudyProgress:
        selected = selected_answer.strip().upper()
        correct = correct_answer.strip().upper()
        progress = self.get_block_progress(block_id)
        progress.answered_questions[question_id] = {
            "selected_answer": selected,
            "correct_answer": correct,
            "is_correct": selected == correct,
            "answered_at": utc_now(),
        }
        progress.last_accessed_at = utc_now()
        return self.save_block_progress(block_id, progress)

    def get_global_stats(self) -> AggregateProgress:
        subjects = self.storage.list_subjects()
        aggregate = AggregateProgress(total_subjects=len(subjects))
        for subject in subjects:
            modules = self.storage.list_modules(subject.slug)
            aggregate.total_modules += len(modules)
            for module in modules:
                blocks = self.storage.list_blocks(subject.slug, module.slug)
                aggregate.total_blocks += len(blocks)
                for block in blocks:
                    progress = self.get_block_progress(block.id)
                    aggregate.total_flashcards += progress.flashcards_total
                    aggregate.total_questions += progress.questions_total
                    aggregate.flashcards_reviewed += progress.flashcards_reviewed
                    aggregate.questions_answered += progress.questions_answered
                    aggregate.questions_correct += progress.questions_correct
                    aggregate.questions_wrong += progress.questions_wrong
                    aggregate.study_time_seconds += progress.study_time_seconds

        work_total = aggregate.total_flashcards + aggregate.total_questions
        work_done = aggregate.flashcards_reviewed + aggregate.questions_answered
        aggregate.progress_percent = int((work_done / work_total) * 100) if work_total else 0
        return aggregate

    def _with_totals(self, progress: StudyProgress, block: StudyBlock) -> StudyProgress:
        progress.flashcards_total = len(block.flashcards)
        progress.questions_total = len(block.questions)
        progress.flashcards_reviewed = len(progress.reviewed_flashcards)
        progress.flashcards_again = len(
            [status for status in progress.reviewed_flashcards.values() if status == "again"]
        )
        progress.flashcards_good = len(
            [status for status in progress.reviewed_flashcards.values() if status == "good"]
        )
        progress.flashcards_easy = len(
            [status for status in progress.reviewed_flashcards.values() if status == "easy"]
        )
        progress.flashcards_mastered = len(
            [
                status
                for status in progress.reviewed_flashcards.values()
                if status in {"easy", "mastered"}
            ]
        )
        progress.flashcards_difficult = len(
            [
                status
                for status in progress.reviewed_flashcards.values()
                if status in {"hard", "difficult", "again"}
            ]
        )
        progress.questions_answered = len(progress.answered_questions)
        progress.questions_correct = len(
            [item for item in progress.answered_questions.values() if item.get("is_correct")]
        )
        progress.questions_wrong = progress.questions_answered - progress.questions_correct
        return progress
