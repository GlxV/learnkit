from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable, Mapping
from typing import Any

from app.application.dto.combined_review import (
    CombinedFlashcardDTO,
    CombinedExamTrapDTO,
    CombinedQuestionDTO,
    CombinedReviewBlockDTO,
    CombinedReviewOriginDTO,
    CombinedReviewSessionDTO,
    CombinedReviewSummaryDTO,
)
from app.application.dto.visual_summary import parse_visual_summary
from app.application.query_services.progress_query_service import ProgressQueryService
from app.core.models.flashcard import Flashcard
from app.core.models.module import Module
from app.core.models.progress import StudyProgress
from app.core.models.question import Question
from app.core.models.study_block import StudyBlock
from app.core.models.subject import Subject
from app.core.storage.local_storage import LocalStorage
from app.application.use_cases.manage_review_cycle import ManageReviewCycleUseCase


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
    def __init__(
        self,
        storage: LocalStorage,
        settings_provider: Callable[[], Mapping[str, object]] | None = None,
    ) -> None:
        self.storage = storage
        self.progress_query_service = ProgressQueryService(storage)
        self.settings_provider = settings_provider or (lambda: {})
        self.review_cycle_use_case = ManageReviewCycleUseCase(storage)

    def block_context(self, block_id: str) -> StudyBlockContextDTO:
        subject, module, block = self.storage.get_block_by_id(block_id)
        return StudyBlockContextDTO(subject=subject, module=module, block=block)

    def flashcard_session(self, block_id: str, include_future: bool = True) -> FlashcardSessionDTO:
        _, _, block = self.storage.get_block_by_id(block_id)
        return FlashcardSessionDTO(
            block=block,
            cards=block.flashcards,
            progress=self.progress_query_service.block_progress(block_id),
            queue=self.progress_query_service.flashcard_queue(
                block_id,
                include_future=include_future,
            ),
        )

    def question_session(self, block_id: str, filter_mode: str = "all") -> QuestionSessionDTO:
        _, _, block = self.storage.get_block_by_id(block_id)
        return QuestionSessionDTO(
            block=block,
            questions=block.questions,
            progress=self.progress_query_service.block_progress(block_id),
            queue=self.progress_query_service.question_queue(block_id, filter_mode),
        )

    def combined_review_session(
        self,
        block_ids: list[str],
        *,
        include_summary: bool = True,
        include_flashcards: bool = True,
        include_questions: bool = True,
        include_exam_traps: bool = True,
        minimum_blocks: int = 2,
    ) -> CombinedReviewSessionDTO:
        unique_ids = list(dict.fromkeys(block_id for block_id in block_ids if block_id))
        if len(unique_ids) < minimum_blocks:
            required = "um bloco" if minimum_blocks == 1 else "dois blocos"
            raise ValueError(f"Selecione pelo menos {required} para revisar juntos.")

        session = CombinedReviewSessionDTO()
        flashcards: dict[tuple[str, str], CombinedFlashcardDTO] = {}
        questions: dict[tuple[str, tuple[tuple[str, str], ...], str], CombinedQuestionDTO] = {}
        exam_traps: dict[tuple[str, str], CombinedExamTrapDTO] = {}
        for block_id in unique_ids:
            subject, module, block = self.storage.get_block_by_id(block_id)
            session.blocks.append(
                CombinedReviewBlockDTO(
                    block_id=block.id,
                    block_title=block.title,
                    subject_name=subject.name,
                    module_name=module.name,
                )
            )
            if include_summary and block.summary and block.summary.content.strip():
                session.summaries.append(
                    CombinedReviewSummaryDTO(
                        block_id=block.id,
                        block_title=block.title,
                        text=block.summary.content,
                    )
                )
            if include_exam_traps:
                self._add_exam_traps(exam_traps, block)
            if include_flashcards:
                cards = block.flashcards
            else:
                cards = []
            for card in cards:
                key = (_normalized(card.question), _normalized(card.answer))
                item = flashcards.setdefault(
                    key,
                    CombinedFlashcardDTO(question=card.question, answer=card.answer),
                )
                item.origins.append(
                    CombinedReviewOriginDTO(
                        block_id=block.id,
                        block_title=block.title,
                        item_id=card.id,
                    )
                )
            if include_questions:
                block_questions = block.questions
            else:
                block_questions = []
            for question in block_questions:
                key = (
                    _normalized(question.statement),
                    tuple(
                        sorted(
                            (letter.upper(), _normalized(text))
                            for letter, text in question.alternatives.items()
                        )
                    ),
                    question.correct_answer.strip().upper(),
                )
                item = questions.setdefault(
                    key,
                    CombinedQuestionDTO(
                        statement=question.statement,
                        alternatives=dict(question.alternatives),
                        correct_answer=question.correct_answer,
                    ),
                )
                item.origins.append(
                    CombinedReviewOriginDTO(
                        block_id=block.id,
                        block_title=block.title,
                        item_id=question.id,
                    )
                )
        session.flashcards = list(flashcards.values())
        session.questions = list(questions.values())
        session.exam_traps = list(exam_traps.values())
        return session

    def _add_exam_traps(
        self,
        target: dict[tuple[str, str], CombinedExamTrapDTO],
        block: StudyBlock,
    ) -> None:
        visual = parse_visual_summary(block.summary_visual)
        if not visual:
            return
        sections = visual.get("sections") if isinstance(visual.get("sections"), list) else []
        for index, section in enumerate(sections):
            if not isinstance(section, dict) or section.get("type") != "exam_trap":
                continue
            title = str(section.get("title") or "Pegadinha de prova").strip()
            text_parts = [str(section.get("text") or "").strip()]
            items = section.get("items") if isinstance(section.get("items"), list) else []
            for item in items:
                if not isinstance(item, dict):
                    text_parts.append(str(item).strip())
                    continue
                item_title = str(item.get("title") or "").strip()
                item_text = str(item.get("text") or "").strip()
                text_parts.append(" - ".join(part for part in (item_title, item_text) if part))
            text = "\n".join(part for part in text_parts if part)
            if not text:
                continue
            key = (_normalized(title), _normalized(text))
            trap = target.setdefault(
                key,
                CombinedExamTrapDTO(title=title, text=text),
            )
            trap.origins.append(
                CombinedReviewOriginDTO(
                    block_id=block.id,
                    block_title=block.title,
                    item_id=f"visual:{index}",
                )
            )

    def record_access(self, block_id: str, duration_seconds: int = 0) -> StudyProgress:
        from app.core.services.progress_service import ProgressService

        progress = ProgressService(self.storage).record_access(block_id, duration_seconds)
        self.review_cycle_use_case.activate_cycle(
            block_id,
            settings=self.settings_provider(),
            automatic=True,
        )
        return progress


def _normalized(value: str) -> str:
    return " ".join(value.split()).casefold()
