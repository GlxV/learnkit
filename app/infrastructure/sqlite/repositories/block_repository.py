from __future__ import annotations

import json
import sqlite3
from typing import Callable

from app.core.models.study_block import StudyBlock
from app.core.models.module import Module
from app.core.models.subject import Subject
from app.infrastructure.sqlite.row_mappers import (
    block_from_row,
    flashcard_from_row,
    module_from_joined_block_row,
    question_from_row,
    subject_from_joined_block_row,
)


class BlockRepository:
    def __init__(self, connect: Callable[[], sqlite3.Connection]) -> None:
        self.connect = connect

    def save(
        self,
        block: StudyBlock,
        module_id: str,
        source_file: str | None = None,
        imported_files_json: str | None = None,
        ai_response_json: str | None = None,
        summary_text: str | None = None,
    ) -> None:
        source_file = source_file if source_file is not None else (
            block.imported_files[0].original_path if block.imported_files else None
        )
        imported_files_json = imported_files_json if imported_files_json is not None else json.dumps(
            [item.to_dict() for item in block.imported_files],
            ensure_ascii=False,
        )
        ai_response_json = ai_response_json if ai_response_json is not None else (
            json.dumps(block.ai_response.to_dict(), ensure_ascii=False) if block.ai_response else None
        )
        summary_text = summary_text if summary_text is not None else (block.summary.content if block.summary else "")
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO study_blocks (
                    id, module_id, slug, title, description, source_file,
                    imported_files_json, extracted_text, generated_prompt, ai_response_raw,
                    ai_response_json, summary_text, summary_visual, preferred_summary_mode,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    slug=excluded.slug,
                    title=excluded.title,
                    description=excluded.description,
                    source_file=excluded.source_file,
                    imported_files_json=excluded.imported_files_json,
                    extracted_text=excluded.extracted_text,
                    generated_prompt=excluded.generated_prompt,
                    ai_response_raw=excluded.ai_response_raw,
                    ai_response_json=excluded.ai_response_json,
                    summary_text=excluded.summary_text,
                    summary_visual=excluded.summary_visual,
                    preferred_summary_mode=excluded.preferred_summary_mode,
                    updated_at=excluded.updated_at
                """,
                (
                    block.id,
                    module_id,
                    block.slug,
                    block.title,
                    block.description,
                    source_file,
                    imported_files_json,
                    block.extracted_content.text,
                    block.generated_prompt,
                    block.ai_response_raw,
                    ai_response_json,
                    summary_text,
                    block.summary_visual,
                    block.preferred_summary_mode or "text",
                    block.created_at,
                    block.updated_at,
                ),
            )
            db.execute("DELETE FROM flashcards WHERE block_id = ?", (block.id,))
            db.executemany(
                """
                INSERT INTO flashcards (
                    id, block_id, question, answer, source, difficulty, status,
                    times_reviewed, last_reviewed_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        card.id,
                        block.id,
                        card.question,
                        card.answer,
                        card.source,
                        None,
                        "new",
                        0,
                        None,
                        block.created_at,
                    )
                    for card in block.flashcards
                ],
            )
            db.execute("DELETE FROM questions WHERE block_id = ?", (block.id,))
            db.executemany(
                """
                INSERT INTO questions (
                    id, block_id, question_text, option_a, option_b, option_c, option_d,
                    correct_option, explanation, user_answer, is_correct, answered_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        question.id,
                        block.id,
                        question.statement,
                        question.alternatives.get("A", ""),
                        question.alternatives.get("B", ""),
                        question.alternatives.get("C", ""),
                        question.alternatives.get("D", ""),
                        question.correct_answer,
                        question.explanation,
                        None,
                        None,
                        None,
                        block.created_at,
                    )
                    for question in block.questions
                ],
            )

    def list_rows(self, module_id: str) -> list[sqlite3.Row]:
        with self.connect() as db:
            return db.execute(
                "SELECT * FROM study_blocks WHERE module_id = ? ORDER BY created_at, title",
                (module_id,),
            ).fetchall()

    def list_blocks(self, module_id: str, subject_id: str) -> list[StudyBlock]:
        return [self._block_from_row(row, subject_id) for row in self.list_rows(module_id)]

    def get_row(self, module_id: str, block_ref: str) -> sqlite3.Row | None:
        with self.connect() as db:
            return db.execute(
                """
                SELECT * FROM study_blocks
                WHERE module_id = ?
                  AND (lower(id)=lower(?) OR lower(slug)=lower(?) OR lower(title)=lower(?))
                LIMIT 1
                """,
                (module_id, block_ref, block_ref, block_ref),
            ).fetchone()

    def get_block(self, module_id: str, block_ref: str, subject_id: str) -> StudyBlock | None:
        row = self.get_row(module_id, block_ref)
        if row is None:
            return None
        return self._block_from_row(row, subject_id)

    def get_by_id_row(self, block_id: str) -> sqlite3.Row | None:
        with self.connect() as db:
            return db.execute(
                """
                SELECT
                    subjects.id AS subject_id,
                    subjects.slug AS subject_slug,
                    subjects.name AS subject_name,
                    subjects.description AS subject_description,
                    subjects.icon AS subject_icon,
                    subjects.color AS subject_color,
                    subjects.created_at AS subject_created_at,
                    subjects.updated_at AS subject_updated_at,
                    modules.id AS module_id,
                    modules.slug AS module_slug,
                    modules.name AS module_name,
                    modules.description AS module_description,
                    modules.created_at AS module_created_at,
                    modules.updated_at AS module_updated_at,
                    study_blocks.*
                FROM study_blocks
                JOIN modules ON modules.id = study_blocks.module_id
                JOIN subjects ON subjects.id = modules.subject_id
                WHERE study_blocks.id = ?
                LIMIT 1
                """,
                (block_id,),
            ).fetchone()

    def get_block_context(self, block_id: str) -> tuple[Subject, Module, StudyBlock] | None:
        row = self.get_by_id_row(block_id)
        if row is None:
            return None
        subject = subject_from_joined_block_row(row)
        module = module_from_joined_block_row(row, subject.id)
        return subject, module, self._block_from_row(row, subject.id)

    def delete(self, block_id: str) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM study_blocks WHERE id = ?", (block_id,))

    def slug_exists(self, module_id: str, slug: str) -> bool:
        with self.connect() as db:
            return (
                db.execute(
                    "SELECT 1 FROM study_blocks WHERE module_id = ? AND slug = ?",
                    (module_id, slug),
                ).fetchone()
                is not None
            )

    def subject_id_for_module(self, module_id: str) -> str:
        with self.connect() as db:
            row = db.execute("SELECT subject_id FROM modules WHERE id = ?", (module_id,)).fetchone()
        return str(row["subject_id"]) if row else ""

    def flashcard_rows(self, block_id: str) -> list[sqlite3.Row]:
        with self.connect() as db:
            return db.execute(
                "SELECT * FROM flashcards WHERE block_id = ? ORDER BY created_at",
                (block_id,),
            ).fetchall()

    def question_rows(self, block_id: str) -> list[sqlite3.Row]:
        with self.connect() as db:
            return db.execute(
                "SELECT * FROM questions WHERE block_id = ? ORDER BY created_at",
                (block_id,),
            ).fetchall()

    def _block_from_row(self, row: sqlite3.Row, subject_id: str) -> StudyBlock:
        return block_from_row(
            row,
            subject_id=subject_id,
            flashcards=[flashcard_from_row(card_row) for card_row in self.flashcard_rows(row["id"])],
            questions=[question_from_row(question_row) for question_row in self.question_rows(row["id"])],
        )
