from __future__ import annotations

import json
import sqlite3
from typing import Callable

from app.core.models.progress import StudyProgress
from app.infrastructure.sqlite.row_mappers import progress_from_row


class ProgressRepository:
    def __init__(self, connect: Callable[[], sqlite3.Connection]) -> None:
        self.connect = connect

    def get_row(self, block_id: str) -> sqlite3.Row | None:
        with self.connect() as db:
            return db.execute("SELECT * FROM study_progress WHERE block_id = ?", (block_id,)).fetchone()

    def get_progress(self, block_id: str) -> StudyProgress:
        return progress_from_row(self.get_row(block_id))

    def save(self, block_id: str, progress: StudyProgress, progress_percent: int | None = None) -> StudyProgress:
        progress_percent = self._progress_percent(progress) if progress_percent is None else progress_percent
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO study_progress (
                    id, block_id, reviewed_flashcards, answered_questions, correct_answers,
                    total_flashcards, total_questions, progress_percent,
                    reviewed_flashcards_json, flashcard_reviews_json, answered_questions_json,
                    question_attempts_json,
                    study_time_seconds, last_accessed_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(block_id) DO UPDATE SET
                    reviewed_flashcards=excluded.reviewed_flashcards,
                    answered_questions=excluded.answered_questions,
                    correct_answers=excluded.correct_answers,
                    total_flashcards=excluded.total_flashcards,
                    total_questions=excluded.total_questions,
                    progress_percent=excluded.progress_percent,
                    reviewed_flashcards_json=excluded.reviewed_flashcards_json,
                    flashcard_reviews_json=excluded.flashcard_reviews_json,
                    answered_questions_json=excluded.answered_questions_json,
                    question_attempts_json=excluded.question_attempts_json,
                    study_time_seconds=excluded.study_time_seconds,
                    last_accessed_at=excluded.last_accessed_at,
                    updated_at=excluded.updated_at
                """,
                (
                    f"progress_{block_id}",
                    block_id,
                    progress.flashcards_reviewed,
                    progress.questions_answered,
                    progress.questions_correct,
                    progress.flashcards_total,
                    progress.questions_total,
                    progress_percent,
                    json.dumps(progress.reviewed_flashcards, ensure_ascii=False),
                    json.dumps(progress.flashcard_reviews, ensure_ascii=False),
                    json.dumps(progress.answered_questions, ensure_ascii=False),
                    json.dumps(progress.question_attempts, ensure_ascii=False),
                    progress.study_time_seconds,
                    progress.last_accessed_at,
                    progress.updated_at,
                ),
            )
            for flashcard_id, status in progress.reviewed_flashcards.items():
                review = progress.flashcard_reviews.get(flashcard_id, {})
                db.execute(
                    """
                    UPDATE flashcards
                    SET status = ?, times_reviewed = ?, last_reviewed_at = ?
                    WHERE id = ?
                    """,
                    (
                        status,
                        int(review.get("times_reviewed", 1)) if isinstance(review, dict) else 1,
                        str(review.get("last_reviewed_at", progress.updated_at)) if isinstance(review, dict) else progress.updated_at,
                        flashcard_id,
                    ),
                )
            for question_id, answer in progress.answered_questions.items():
                db.execute(
                    """
                    UPDATE questions
                    SET user_answer = ?, is_correct = ?, answered_at = ?
                    WHERE id = ?
                    """,
                    (
                        answer.get("selected_answer"),
                        1 if answer.get("is_correct") else 0,
                        answer.get("answered_at"),
                        question_id,
                    ),
                )
        return progress

    def delete_for_block(self, block_id: str) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM study_progress WHERE block_id = ?", (block_id,))

    def _progress_percent(self, progress: StudyProgress) -> int:
        total = progress.flashcards_total + progress.questions_total
        done = progress.flashcards_reviewed + progress.questions_answered
        return int((done / total) * 100) if total else 0
