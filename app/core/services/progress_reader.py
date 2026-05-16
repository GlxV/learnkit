from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.core.models.progress import AggregateProgress, StudyProgress
from app.core.models.study_block import StudyBlock
from app.core.storage.local_storage import LocalStorage


class ProgressReader:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage

    def block_progress(self, block_id: str) -> StudyProgress:
        subject, module, block = self.storage.get_block_by_id(block_id)
        if hasattr(self.storage, "get_progress"):
            progress = self.storage.get_progress(block_id)
        else:
            path = self.storage.block_path(subject.slug, module.slug, block.slug) / "progress.json"
            progress = StudyProgress.from_dict(
                json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
            )
        return self.with_totals(progress, block)

    def flashcard_queue(self, block_id: str, include_future: bool = True) -> list[dict[str, Any]]:
        _, _, block = self.storage.get_block_by_id(block_id)
        progress = self.block_progress(block_id)
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
                    "interval_days": (
                        int(review.get("interval_days", 0)) if isinstance(review, dict) else 0
                    ),
                    "_sort": (group, due_at or "", index),
                }
            )
        queue.sort(key=lambda item: item["_sort"])
        for item in queue:
            item.pop("_sort", None)
        return queue

    def question_queue(self, block_id: str, filter_mode: str = "all") -> list[dict[str, Any]]:
        _, _, block = self.storage.get_block_by_id(block_id)
        progress = self.block_progress(block_id)
        valid_filters = {"all", "unanswered", "wrong", "correct"}
        selected_filter = filter_mode if filter_mode in valid_filters else "all"
        queue: list[dict[str, Any]] = []
        order = {"unanswered": 0, "wrong": 1, "correct": 2}
        for index, question in enumerate(block.questions):
            answer = progress.answered_questions.get(question.id)
            if not answer:
                state = "unanswered"
            elif answer.get("is_correct"):
                state = "correct"
            else:
                state = "wrong"
            if selected_filter != "all" and state != selected_filter:
                continue
            attempts = progress.question_attempts.get(question.id, [])
            queue.append(
                {
                    "question_id": question.id,
                    "index": index,
                    "state": state,
                    "selected_answer": answer.get("selected_answer") if answer else "",
                    "correct_answer": question.correct_answer,
                    "attempts": len(attempts),
                    "last_answered_at": answer.get("answered_at") if answer else "",
                    "_sort": (order[state], index),
                }
            )
        queue.sort(key=lambda item: item["_sort"])
        for item in queue:
            item.pop("_sort", None)
        return queue

    def global_stats(self) -> AggregateProgress:
        subjects = self.storage.list_subjects()
        aggregate = AggregateProgress(total_subjects=len(subjects))
        for subject in subjects:
            modules = self.storage.list_modules(subject.slug)
            aggregate.total_modules += len(modules)
            for module in modules:
                blocks = self.storage.list_blocks(subject.slug, module.slug)
                aggregate.total_blocks += len(blocks)
                for block in blocks:
                    progress = self.block_progress(block.id)
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

    def review_dashboard(self, subject_ref: str | None = None) -> dict[str, Any]:
        subjects = self.storage.list_subjects()
        if subject_ref:
            try:
                selected = self.storage.get_subject(subject_ref)
                subjects = [selected]
            except ValueError:
                subjects = []

        summary = {
            "due_flashcards": 0,
            "new_flashcards": 0,
            "future_flashcards": 0,
            "wrong_questions": 0,
            "correct_questions": 0,
            "unanswered_questions": 0,
            "pending_reviews": 0,
        }
        blocks: list[dict[str, Any]] = []
        activity: list[dict[str, Any]] = []

        for subject in subjects:
            for module in self.storage.list_modules(subject.slug):
                for block in self.storage.list_blocks(subject.slug, module.slug):
                    progress = self.block_progress(block.id)
                    flashcards = self.flashcard_queue(block.id)
                    questions_all = self.question_queue(block.id, "all")
                    question_counts = {
                        "wrong": len([item for item in questions_all if item["state"] == "wrong"]),
                        "correct": len(
                            [item for item in questions_all if item["state"] == "correct"]
                        ),
                        "unanswered": len(
                            [item for item in questions_all if item["state"] == "unanswered"]
                        ),
                    }
                    flashcard_counts = {
                        "due": len([item for item in flashcards if item["state"] == "due"]),
                        "new": len([item for item in flashcards if item["state"] == "new"]),
                        "future": len([item for item in flashcards if item["state"] == "future"]),
                    }
                    summary["due_flashcards"] += flashcard_counts["due"]
                    summary["new_flashcards"] += flashcard_counts["new"]
                    summary["future_flashcards"] += flashcard_counts["future"]
                    summary["wrong_questions"] += question_counts["wrong"]
                    summary["correct_questions"] += question_counts["correct"]
                    summary["unanswered_questions"] += question_counts["unanswered"]
                    pending = (
                        flashcard_counts["due"]
                        + flashcard_counts["new"]
                        + question_counts["wrong"]
                        + question_counts["unanswered"]
                    )
                    summary["pending_reviews"] += pending

                    total_items = progress.flashcards_total + progress.questions_total
                    done_items = progress.flashcards_reviewed + progress.questions_answered
                    percent = int((done_items / total_items) * 100) if total_items else 0
                    if total_items or pending:
                        blocks.append(
                            {
                                "subject_name": subject.name,
                                "module_name": module.name,
                                "block_id": block.id,
                                "block_title": block.title,
                                "progress_percent": percent,
                                "due_flashcards": flashcard_counts["due"],
                                "new_flashcards": flashcard_counts["new"],
                                "future_flashcards": flashcard_counts["future"],
                                "wrong_questions": question_counts["wrong"],
                                "unanswered_questions": question_counts["unanswered"],
                                "correct_questions": question_counts["correct"],
                                "pending_reviews": pending,
                                "last_accessed_at": progress.last_accessed_at or "",
                                "updated_at": progress.updated_at,
                            }
                        )
                    activity.extend(
                        self._activity_for_block(subject.name, module.name, block, progress)
                    )

        blocks.sort(key=lambda item: (item["pending_reviews"], item["updated_at"]), reverse=True)
        activity.sort(key=lambda item: item.get("occurred_at", ""), reverse=True)
        return {
            "summary": summary,
            "blocks": blocks,
            "activity": activity[:20],
        }

    def with_totals(self, progress: StudyProgress, block: StudyBlock) -> StudyProgress:
        valid_flashcards = {card.id for card in block.flashcards}
        valid_questions = {question.id for question in block.questions}
        progress.reviewed_flashcards = {
            card_id: status
            for card_id, status in progress.reviewed_flashcards.items()
            if card_id in valid_flashcards
        }
        progress.flashcard_reviews = {
            card_id: review
            for card_id, review in progress.flashcard_reviews.items()
            if card_id in valid_flashcards
        }
        progress.answered_questions = {
            question_id: answer
            for question_id, answer in progress.answered_questions.items()
            if question_id in valid_questions
        }
        progress.question_attempts = {
            question_id: attempts
            for question_id, attempts in progress.question_attempts.items()
            if question_id in valid_questions
        }
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

    def _activity_for_block(
        self,
        subject_name: str,
        module_name: str,
        block: StudyBlock,
        progress: StudyProgress,
    ) -> list[dict[str, Any]]:
        activity: list[dict[str, Any]] = []
        cards_by_id = {card.id: card for card in block.flashcards}
        questions_by_id = {question.id: question for question in block.questions}

        for card_id, review in progress.flashcard_reviews.items():
            if not isinstance(review, dict):
                continue
            card = cards_by_id.get(card_id)
            activity.append(
                {
                    "type": "flashcard",
                    "subject_name": subject_name,
                    "module_name": module_name,
                    "block_id": block.id,
                    "block_title": block.title,
                    "title": (card.question if card else "Flashcard")[:90],
                    "detail": f"Marcado como {review.get('status', 'revisado')}",
                    "occurred_at": str(review.get("last_reviewed_at", "")),
                }
            )

        for question_id, attempts in progress.question_attempts.items():
            if not isinstance(attempts, list):
                continue
            question = questions_by_id.get(question_id)
            for attempt in attempts[-5:]:
                if not isinstance(attempt, dict):
                    continue
                activity.append(
                    {
                        "type": "question",
                        "subject_name": subject_name,
                        "module_name": module_name,
                        "block_id": block.id,
                        "block_title": block.title,
                        "title": (question.statement if question else "Pergunta")[:90],
                        "detail": (
                            "Resposta correta"
                            if attempt.get("is_correct")
                            else "Resposta incorreta"
                        ),
                        "occurred_at": str(attempt.get("answered_at", "")),
                    }
                )

        if progress.last_accessed_at:
            activity.append(
                {
                    "type": "access",
                    "subject_name": subject_name,
                    "module_name": module_name,
                    "block_id": block.id,
                    "block_title": block.title,
                    "title": block.title,
                    "detail": "Bloco acessado",
                    "occurred_at": progress.last_accessed_at,
                }
            )
        return activity
