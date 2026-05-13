from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.models.base import require_dict, utc_now


@dataclass(slots=True)
class StudyProgress:
    flashcards_total: int = 0
    flashcards_reviewed: int = 0
    flashcards_mastered: int = 0
    flashcards_difficult: int = 0
    flashcards_again: int = 0
    flashcards_good: int = 0
    flashcards_easy: int = 0
    questions_total: int = 0
    questions_answered: int = 0
    questions_correct: int = 0
    questions_wrong: int = 0
    answered_questions: dict[str, dict[str, Any]] = field(default_factory=dict)
    question_attempts: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    reviewed_flashcards: dict[str, str] = field(default_factory=dict)
    flashcard_reviews: dict[str, dict[str, Any]] = field(default_factory=dict)
    study_time_seconds: int = 0
    last_accessed_at: str | None = None
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "flashcards_total": self.flashcards_total,
            "flashcards_reviewed": self.flashcards_reviewed,
            "flashcards_mastered": self.flashcards_mastered,
            "flashcards_difficult": self.flashcards_difficult,
            "flashcards_again": self.flashcards_again,
            "flashcards_good": self.flashcards_good,
            "flashcards_easy": self.flashcards_easy,
            "questions_total": self.questions_total,
            "questions_answered": self.questions_answered,
            "questions_correct": self.questions_correct,
            "questions_wrong": self.questions_wrong,
            "answered_questions": self.answered_questions,
            "question_attempts": self.question_attempts,
            "reviewed_flashcards": self.reviewed_flashcards,
            "flashcard_reviews": self.flashcard_reviews,
            "study_time_seconds": self.study_time_seconds,
            "last_accessed_at": self.last_accessed_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "StudyProgress":
        safe = require_dict(data)
        return cls(
            flashcards_total=int(safe.get("flashcards_total", 0)),
            flashcards_reviewed=int(safe.get("flashcards_reviewed", 0)),
            flashcards_mastered=int(safe.get("flashcards_mastered", 0)),
            flashcards_difficult=int(safe.get("flashcards_difficult", 0)),
            flashcards_again=int(safe.get("flashcards_again", 0)),
            flashcards_good=int(safe.get("flashcards_good", 0)),
            flashcards_easy=int(safe.get("flashcards_easy", 0)),
            questions_total=int(safe.get("questions_total", 0)),
            questions_answered=int(safe.get("questions_answered", 0)),
            questions_correct=int(safe.get("questions_correct", 0)),
            questions_wrong=int(safe.get("questions_wrong", 0)),
            answered_questions=dict(safe.get("answered_questions", {})),
            question_attempts=dict(safe.get("question_attempts", {})),
            reviewed_flashcards=dict(safe.get("reviewed_flashcards", {})),
            flashcard_reviews=dict(safe.get("flashcard_reviews", {})),
            study_time_seconds=int(safe.get("study_time_seconds", 0)),
            last_accessed_at=safe.get("last_accessed_at"),
            updated_at=str(safe.get("updated_at", utc_now())),
        )


@dataclass(slots=True)
class AggregateProgress:
    total_subjects: int = 0
    total_modules: int = 0
    total_blocks: int = 0
    total_flashcards: int = 0
    total_questions: int = 0
    flashcards_reviewed: int = 0
    questions_answered: int = 0
    questions_correct: int = 0
    questions_wrong: int = 0
    progress_percent: int = 0
    study_time_seconds: int = 0
