from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CombinedReviewBlockDTO:
    block_id: str
    block_title: str
    subject_name: str
    module_name: str


@dataclass(frozen=True, slots=True)
class CombinedReviewOriginDTO:
    block_id: str
    block_title: str
    item_id: str


@dataclass(frozen=True, slots=True)
class CombinedReviewSummaryDTO:
    block_id: str
    block_title: str
    text: str


@dataclass(slots=True)
class CombinedFlashcardDTO:
    question: str
    answer: str
    origins: list[CombinedReviewOriginDTO] = field(default_factory=list)


@dataclass(slots=True)
class CombinedQuestionDTO:
    statement: str
    alternatives: dict[str, str]
    correct_answer: str
    origins: list[CombinedReviewOriginDTO] = field(default_factory=list)


@dataclass(slots=True)
class CombinedReviewSessionDTO:
    blocks: list[CombinedReviewBlockDTO] = field(default_factory=list)
    summaries: list[CombinedReviewSummaryDTO] = field(default_factory=list)
    flashcards: list[CombinedFlashcardDTO] = field(default_factory=list)
    questions: list[CombinedQuestionDTO] = field(default_factory=list)
