from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.models.base import utc_now
from app.core.models.progress import AggregateProgress, StudyProgress
from app.core.models.study_block import StudyBlock
from app.core.storage.local_storage import LocalStorage


class ProgressService:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage

    def get_block_progress(self, block_id: str) -> StudyProgress:
        subject, module, block = self.storage.get_block_by_id(block_id)
        if hasattr(self.storage, "get_progress"):
            progress = self.storage.get_progress(block_id)
        else:
            path = self.storage.block_path(subject.slug, module.slug, block.slug) / "progress.json"
            progress = StudyProgress.from_dict(
                json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
            )
        return self._with_totals(progress, block)

    def save_block_progress(self, block_id: str, progress: StudyProgress) -> StudyProgress:
        subject, module, block = self.storage.get_block_by_id(block_id)
        progress = self._with_totals(progress, block)
        progress.updated_at = utc_now()
        if hasattr(self.storage, "save_progress"):
            return self.storage.save_progress(block_id, progress)
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
        progress.flashcard_reviews[flashcard_id] = self._next_flashcard_review(
            progress.flashcard_reviews.get(flashcard_id, {}),
            normalized,
        )
        progress.last_accessed_at = utc_now()
        return self.save_block_progress(block_id, progress)

    def get_flashcard_queue(self, block_id: str, include_future: bool = True) -> list[dict[str, Any]]:
        _, _, block = self.storage.get_block_by_id(block_id)
        progress = self.get_block_progress(block_id)
        now = datetime.now(timezone.utc)
        queue: list[dict[str, Any]] = []
        for index, card in enumerate(block.flashcards):
            review = progress.flashcard_reviews.get(card.id, {})
            due_at = str(review.get("due_at", "")) if isinstance(review, dict) else ""
            due_dt = self._parse_datetime(due_at)
            if not review:
                state = "new"
                group = 1
            elif due_dt is None or due_dt <= now:
                state = "due"
                group = 0
            else:
                state = "future"
                group = 2
            if state == "future" and not include_future:
                continue
            queue.append(
                {
                    "card_id": card.id,
                    "index": index,
                    "state": state,
                    "status": review.get("status", "new") if isinstance(review, dict) else "new",
                    "due_at": due_at,
                    "interval_days": int(review.get("interval_days", 0)) if isinstance(review, dict) else 0,
                    "_sort": (group, due_at or "", index),
                }
            )
        queue.sort(key=lambda item: item["_sort"])
        for item in queue:
            item.pop("_sort", None)
        return queue

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

    def _next_flashcard_review(self, current: dict[str, Any], status: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        previous_interval = int(current.get("interval_days", 0) or 0) if isinstance(current, dict) else 0
        ease = float(current.get("ease_factor", 2.5) or 2.5) if isinstance(current, dict) else 2.5
        times = int(current.get("times_reviewed", 0) or 0) if isinstance(current, dict) else 0

        if status == "again":
            interval_days = 0
            ease = max(1.3, ease - 0.2)
        elif status == "hard":
            interval_days = 1 if previous_interval < 1 else max(1, round(previous_interval * 1.2))
            ease = max(1.3, ease - 0.15)
        elif status == "good":
            interval_days = 1 if times == 0 else max(previous_interval + 1, round(previous_interval * ease))
        elif status == "easy":
            interval_days = 4 if times == 0 else max(previous_interval + 2, round(previous_interval * ease * 1.3))
            ease = min(3.2, ease + 0.15)
        else:
            interval_days = previous_interval

        due_at = now if interval_days == 0 else now + timedelta(days=interval_days)
        return {
            "status": status,
            "times_reviewed": times + 1,
            "ease_factor": round(ease, 2),
            "interval_days": interval_days,
            "last_reviewed_at": now.isoformat(),
            "due_at": due_at.isoformat(),
        }

    def _parse_datetime(self, value: str) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
