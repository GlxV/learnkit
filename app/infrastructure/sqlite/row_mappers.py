from __future__ import annotations

import json
import sqlite3
from typing import Any

from app.core.models.ai_response import AIResponse
from app.core.models.extracted_content import ExtractedContent
from app.core.models.flashcard import Flashcard
from app.core.models.imported_file import ImportedFile
from app.core.models.module import Module
from app.core.models.progress import StudyProgress
from app.core.models.question import Question
from app.core.models.review_schedule import ReviewSchedule
from app.core.models.study_block import StudyBlock
from app.core.models.subject import Subject
from app.core.models.summary import Summary


def subject_from_row(row: sqlite3.Row, module_slugs: list[str] | None = None) -> Subject:
    subject = Subject(
        id=row["id"],
        slug=row["slug"],
        name=row["name"],
        description=row["description"],
        icon=row["icon"],
        color=row["color"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
    subject.modules = module_slugs or []
    return subject


def module_from_row(row: sqlite3.Row, block_slugs: list[str] | None = None) -> Module:
    module = Module(
        id=row["id"],
        subject_id=row["subject_id"],
        slug=row["slug"],
        name=row["name"],
        description=row["description"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
    module.study_blocks = block_slugs or []
    return module


def subject_from_joined_block_row(row: sqlite3.Row) -> Subject:
    return Subject(
        id=row["subject_id"],
        slug=row["subject_slug"],
        name=row["subject_name"],
        description=row["subject_description"],
        icon=row["subject_icon"],
        color=row["subject_color"],
        created_at=row["subject_created_at"],
        updated_at=row["subject_updated_at"],
    )


def module_from_joined_block_row(row: sqlite3.Row, subject_id: str) -> Module:
    return Module(
        id=row["module_id"],
        subject_id=subject_id,
        slug=row["module_slug"],
        name=row["module_name"],
        description=row["module_description"],
        created_at=row["module_created_at"],
        updated_at=row["module_updated_at"],
    )


def block_from_row(
    row: sqlite3.Row,
    subject_id: str,
    flashcards: list[Flashcard] | None = None,
    questions: list[Question] | None = None,
) -> StudyBlock:
    imported_files = [
        ImportedFile.from_dict(item)
        for item in _json_list(row["imported_files_json"])
        if isinstance(item, dict)
    ]
    block = StudyBlock(
        id=row["id"],
        subject_id=subject_id,
        module_id=row["module_id"],
        slug=row["slug"],
        title=row["title"],
        description=row["description"],
        imported_files=imported_files,
        extracted_content=ExtractedContent(
            text=row["extracted_text"] or "",
            source_files=[item.file_name for item in imported_files],
        ),
        generated_prompt=row["generated_prompt"] or "",
        ai_response_raw=row["ai_response_raw"] or "",
        ai_response=AIResponse.from_dict(_json_dict(row["ai_response_json"])),
        summary=Summary(row["summary_text"]) if row["summary_text"] else None,
        summary_visual=row["summary_visual"] or "",
        preferred_summary_mode=row["preferred_summary_mode"] or "text",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
    block.flashcards = flashcards or []
    block.questions = questions or []
    return block


def flashcard_from_row(row: sqlite3.Row) -> Flashcard:
    return Flashcard(id=row["id"], question=row["question"], answer=row["answer"], source=row["source"])


def question_from_row(row: sqlite3.Row) -> Question:
    return Question(
        id=row["id"],
        statement=row["question_text"],
        alternatives={
            "A": row["option_a"] or "",
            "B": row["option_b"] or "",
            "C": row["option_c"] or "",
            "D": row["option_d"] or "",
        },
        correct_answer=row["correct_option"] or "",
        explanation=row["explanation"],
    )


def progress_from_row(row: sqlite3.Row | None) -> StudyProgress:
    if row is None:
        return StudyProgress()
    return StudyProgress.from_dict(
        {
            "flashcards_total": row["total_flashcards"],
            "flashcards_reviewed": row["reviewed_flashcards"],
            "questions_total": row["total_questions"],
            "questions_answered": row["answered_questions"],
            "questions_correct": row["correct_answers"],
            "reviewed_flashcards": _json_dict(row["reviewed_flashcards_json"]) or {},
            "flashcard_reviews": _json_dict(row["flashcard_reviews_json"]) or {},
            "answered_questions": _json_dict(row["answered_questions_json"]) or {},
            "question_attempts": _json_dict(row["question_attempts_json"]) or {},
            "study_time_seconds": row["study_time_seconds"] or 0,
            "last_accessed_at": row["last_accessed_at"],
            "updated_at": row["updated_at"],
        }
    )


def review_schedule_from_row(row: sqlite3.Row) -> ReviewSchedule:
    return ReviewSchedule(
        id=row["id"],
        study_block_id=row["study_block_id"],
        subject_id=row["subject_id"],
        module_id=row["module_id"],
        review_step=row["review_step"],
        scheduled_at=row["scheduled_at"],
        completed_at=row["completed_at"],
        status=row["status"],
        created_at=row["created_at"],
    )


def _json_list(raw: str | None) -> list[Any]:
    try:
        value = json.loads(raw or "[]")
        return value if isinstance(value, list) else []
    except json.JSONDecodeError:
        return []


def _json_dict(raw: str | None) -> dict[str, Any] | None:
    try:
        value = json.loads(raw or "null")
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None
