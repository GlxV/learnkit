from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class FlashcardQueueItemDTO:
    card_id: str
    index: int
    state: str
    status: str
    due_at: str = ""
    interval_days: int = 0

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "FlashcardQueueItemDTO":
        return cls(
            card_id=str(data.get("card_id", "")),
            index=int(data.get("index", 0)),
            state=str(data.get("state", "")),
            status=str(data.get("status", "new")),
            due_at=str(data.get("due_at", "")),
            interval_days=int(data.get("interval_days", 0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_id": self.card_id,
            "index": self.index,
            "state": self.state,
            "status": self.status,
            "due_at": self.due_at,
            "interval_days": self.interval_days,
        }


@dataclass(frozen=True, slots=True)
class QuestionQueueItemDTO:
    question_id: str
    index: int
    state: str
    selected_answer: str = ""
    correct_answer: str = ""
    attempts: int = 0
    last_answered_at: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "QuestionQueueItemDTO":
        return cls(
            question_id=str(data.get("question_id", "")),
            index=int(data.get("index", 0)),
            state=str(data.get("state", "")),
            selected_answer=str(data.get("selected_answer", "")),
            correct_answer=str(data.get("correct_answer", "")),
            attempts=int(data.get("attempts", 0)),
            last_answered_at=str(data.get("last_answered_at", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "index": self.index,
            "state": self.state,
            "selected_answer": self.selected_answer,
            "correct_answer": self.correct_answer,
            "attempts": self.attempts,
            "last_answered_at": self.last_answered_at,
        }


@dataclass(frozen=True, slots=True)
class ReviewDashboardSummaryDTO:
    due_flashcards: int = 0
    new_flashcards: int = 0
    future_flashcards: int = 0
    wrong_questions: int = 0
    correct_questions: int = 0
    unanswered_questions: int = 0
    pending_reviews: int = 0

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ReviewDashboardSummaryDTO":
        return cls(
            due_flashcards=int(data.get("due_flashcards", 0)),
            new_flashcards=int(data.get("new_flashcards", 0)),
            future_flashcards=int(data.get("future_flashcards", 0)),
            wrong_questions=int(data.get("wrong_questions", 0)),
            correct_questions=int(data.get("correct_questions", 0)),
            unanswered_questions=int(data.get("unanswered_questions", 0)),
            pending_reviews=int(data.get("pending_reviews", 0)),
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "due_flashcards": self.due_flashcards,
            "new_flashcards": self.new_flashcards,
            "future_flashcards": self.future_flashcards,
            "wrong_questions": self.wrong_questions,
            "correct_questions": self.correct_questions,
            "unanswered_questions": self.unanswered_questions,
            "pending_reviews": self.pending_reviews,
        }


@dataclass(frozen=True, slots=True)
class ReviewDashboardBlockDTO:
    subject_name: str
    module_name: str
    block_id: str
    block_title: str
    progress_percent: int
    due_flashcards: int
    new_flashcards: int
    future_flashcards: int
    wrong_questions: int
    unanswered_questions: int
    correct_questions: int
    pending_reviews: int
    last_accessed_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ReviewDashboardBlockDTO":
        return cls(
            subject_name=str(data.get("subject_name", "")),
            module_name=str(data.get("module_name", "")),
            block_id=str(data.get("block_id", "")),
            block_title=str(data.get("block_title", "")),
            progress_percent=int(data.get("progress_percent", 0)),
            due_flashcards=int(data.get("due_flashcards", 0)),
            new_flashcards=int(data.get("new_flashcards", 0)),
            future_flashcards=int(data.get("future_flashcards", 0)),
            wrong_questions=int(data.get("wrong_questions", 0)),
            unanswered_questions=int(data.get("unanswered_questions", 0)),
            correct_questions=int(data.get("correct_questions", 0)),
            pending_reviews=int(data.get("pending_reviews", 0)),
            last_accessed_at=str(data.get("last_accessed_at", "")),
            updated_at=str(data.get("updated_at", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_name": self.subject_name,
            "module_name": self.module_name,
            "block_id": self.block_id,
            "block_title": self.block_title,
            "progress_percent": self.progress_percent,
            "due_flashcards": self.due_flashcards,
            "new_flashcards": self.new_flashcards,
            "future_flashcards": self.future_flashcards,
            "wrong_questions": self.wrong_questions,
            "unanswered_questions": self.unanswered_questions,
            "correct_questions": self.correct_questions,
            "pending_reviews": self.pending_reviews,
            "last_accessed_at": self.last_accessed_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True, slots=True)
class ReviewActivityDTO:
    type: str
    subject_name: str
    module_name: str
    block_id: str
    block_title: str
    title: str
    detail: str
    occurred_at: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ReviewActivityDTO":
        return cls(
            type=str(data.get("type", "")),
            subject_name=str(data.get("subject_name", "")),
            module_name=str(data.get("module_name", "")),
            block_id=str(data.get("block_id", "")),
            block_title=str(data.get("block_title", "")),
            title=str(data.get("title", "")),
            detail=str(data.get("detail", "")),
            occurred_at=str(data.get("occurred_at", "")),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "type": self.type,
            "subject_name": self.subject_name,
            "module_name": self.module_name,
            "block_id": self.block_id,
            "block_title": self.block_title,
            "title": self.title,
            "detail": self.detail,
            "occurred_at": self.occurred_at,
        }


@dataclass(frozen=True, slots=True)
class ReviewDashboardDTO:
    summary: ReviewDashboardSummaryDTO = field(default_factory=ReviewDashboardSummaryDTO)
    blocks: list[ReviewDashboardBlockDTO] = field(default_factory=list)
    activity: list[ReviewActivityDTO] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ReviewDashboardDTO":
        blocks = data.get("blocks", [])
        activity = data.get("activity", [])
        return cls(
            summary=ReviewDashboardSummaryDTO.from_mapping(data.get("summary", {})),
            blocks=[
                ReviewDashboardBlockDTO.from_mapping(item)
                for item in blocks
                if isinstance(item, Mapping)
            ],
            activity=[
                ReviewActivityDTO.from_mapping(item)
                for item in activity
                if isinstance(item, Mapping)
            ],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "blocks": [block.to_dict() for block in self.blocks],
            "activity": [item.to_dict() for item in self.activity],
        }
