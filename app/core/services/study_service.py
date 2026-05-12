from __future__ import annotations

from dataclasses import dataclass

from app.core.models.flashcard import Flashcard
from app.core.models.question import Question
from app.core.models.summary import Summary
from app.core.storage.local_storage import LocalStorage


@dataclass(slots=True)
class StudySession:
    scope: str
    title: str
    summaries: list[Summary]
    flashcards: list[Flashcard]
    questions: list[Question]


class StudyService:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage

    def study_block(self, subject_ref: str, module_ref: str, block_ref: str) -> StudySession:
        _, _, block = self.storage.get_block(subject_ref, module_ref, block_ref)
        return StudySession(
            scope="block",
            title=block.title,
            summaries=[block.summary] if block.summary else [],
            flashcards=block.flashcards,
            questions=block.questions,
        )

    def study_module(self, subject_ref: str, module_ref: str) -> StudySession:
        _, module = self.storage.get_module(subject_ref, module_ref)
        blocks = self.storage.list_blocks(subject_ref, module.slug)
        return StudySession(
            scope="module",
            title=module.name,
            summaries=[block.summary for block in blocks if block.summary],
            flashcards=[card for block in blocks for card in block.flashcards],
            questions=[question for block in blocks for question in block.questions],
        )

    def study_subject(self, subject_ref: str) -> StudySession:
        subject = self.storage.get_subject(subject_ref)
        modules = self.storage.list_modules(subject.slug)
        blocks = [
            block
            for module in modules
            for block in self.storage.list_blocks(subject.slug, module.slug)
        ]
        return StudySession(
            scope="subject",
            title=subject.name,
            summaries=[block.summary for block in blocks if block.summary],
            flashcards=[card for block in blocks for card in block.flashcards],
            questions=[question for block in blocks for question in block.questions],
        )

    def list_module_summaries(self, subject_ref: str, module_ref: str) -> list[Summary]:
        return self.study_module(subject_ref, module_ref).summaries

    def list_module_flashcards(self, subject_ref: str, module_ref: str) -> list[Flashcard]:
        return self.study_module(subject_ref, module_ref).flashcards

    def list_module_questions(self, subject_ref: str, module_ref: str) -> list[Question]:
        return self.study_module(subject_ref, module_ref).questions

    def list_subject_summaries(self, subject_ref: str) -> list[Summary]:
        return self.study_subject(subject_ref).summaries

    def list_subject_flashcards(self, subject_ref: str) -> list[Flashcard]:
        return self.study_subject(subject_ref).flashcards

    def list_subject_questions(self, subject_ref: str) -> list[Question]:
        return self.study_subject(subject_ref).questions
