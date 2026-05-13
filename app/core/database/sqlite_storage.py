from __future__ import annotations

import json
import sqlite3
import shutil
from pathlib import Path
from typing import Any

from app.core.models.ai_response import AIResponse
from app.core.models.extracted_content import ExtractedContent
from app.core.models.flashcard import Flashcard
from app.core.models.imported_file import ImportedFile
from app.core.models.module import Module
from app.core.models.progress import StudyProgress
from app.core.models.question import Question
from app.core.models.study_block import StudyBlock
from app.core.models.subject import Subject
from app.core.models.summary import Summary
from app.core.storage.local_storage import LocalStorage, slugify


class SQLiteStorage:
    def __init__(self, db_path: str | Path = "data/learnkit.db", migrate_json: bool = True) -> None:
        self.db_path = Path(db_path)
        self.base_path = self.db_path.parent
        self.subjects_path = self.base_path / "subjects"
        self.files_path = self.base_path / "sqlite_files"
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.files_path.mkdir(parents=True, exist_ok=True)
        self._initialize()
        if migrate_json:
            self._migrate_json_if_empty()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def create_subject(
        self,
        name: str,
        description: str | None = None,
        icon: str | None = None,
        color: str | None = None,
    ) -> Subject:
        slug = self.make_unique_subject_slug(name)
        subject = Subject(name=name, slug=slug, description=description, icon=icon, color=color)
        self.save_subject(subject)
        return subject

    def save_subject(self, subject: Subject) -> None:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO subjects (id, slug, name, description, icon, color, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    slug=excluded.slug,
                    name=excluded.name,
                    description=excluded.description,
                    icon=excluded.icon,
                    color=excluded.color,
                    updated_at=excluded.updated_at
                """,
                (
                    subject.id,
                    subject.slug,
                    subject.name,
                    subject.description,
                    subject.icon,
                    subject.color,
                    subject.created_at,
                    subject.updated_at,
                ),
            )

    def list_subjects(self) -> list[Subject]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM subjects ORDER BY created_at, name").fetchall()
        return [self._subject_from_row(row) for row in rows]

    def get_subject(self, subject_ref: str) -> Subject:
        with self.connect() as db:
            row = db.execute(
                """
                SELECT * FROM subjects
                WHERE lower(id)=lower(?) OR lower(slug)=lower(?) OR lower(name)=lower(?)
                LIMIT 1
                """,
                (subject_ref, subject_ref, subject_ref),
            ).fetchone()
        if row is None:
            raise ValueError(f"Materia nao encontrada: {subject_ref}")
        return self._subject_from_row(row)

    def delete_subject(self, subject_ref: str) -> None:
        subject = self.get_subject(subject_ref)
        with self.connect() as db:
            db.execute("DELETE FROM subjects WHERE id = ?", (subject.id,))
        shutil.rmtree(self.subject_path(subject.slug), ignore_errors=True)

    def create_module(
        self,
        subject_ref: str,
        name: str,
        description: str | None = None,
    ) -> Module:
        subject = self.get_subject(subject_ref)
        slug = self.make_unique_module_slug(subject.id, name)
        module = Module(subject_id=subject.id, name=name, slug=slug, description=description)
        self.save_module(subject, module)
        return module

    def save_module(self, subject: Subject, module: Module) -> None:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO modules (id, subject_id, slug, name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    slug=excluded.slug,
                    name=excluded.name,
                    description=excluded.description,
                    updated_at=excluded.updated_at
                """,
                (
                    module.id,
                    subject.id,
                    module.slug,
                    module.name,
                    module.description,
                    module.created_at,
                    module.updated_at,
                ),
            )

    def list_modules(self, subject_ref: str) -> list[Module]:
        subject = self.get_subject(subject_ref)
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM modules WHERE subject_id = ? ORDER BY created_at, name",
                (subject.id,),
            ).fetchall()
        return [self._module_from_row(row) for row in rows]

    def get_module(self, subject_ref: str, module_ref: str) -> tuple[Subject, Module]:
        subject = self.get_subject(subject_ref)
        with self.connect() as db:
            row = db.execute(
                """
                SELECT * FROM modules
                WHERE subject_id = ?
                  AND (lower(id)=lower(?) OR lower(slug)=lower(?) OR lower(name)=lower(?))
                LIMIT 1
                """,
                (subject.id, module_ref, module_ref, module_ref),
            ).fetchone()
        if row is None:
            raise ValueError(f"Modulo nao encontrado: {module_ref}")
        return subject, self._module_from_row(row)

    def delete_module(self, subject_ref: str, module_ref: str) -> None:
        subject, module = self.get_module(subject_ref, module_ref)
        with self.connect() as db:
            db.execute("DELETE FROM modules WHERE id = ?", (module.id,))
        shutil.rmtree(self.module_path(subject.slug, module.slug), ignore_errors=True)

    def create_block(
        self,
        subject_ref: str,
        module_ref: str,
        title: str,
        description: str | None = None,
    ) -> StudyBlock:
        subject, module = self.get_module(subject_ref, module_ref)
        slug = self.make_unique_block_slug(module.id, title)
        block = StudyBlock(
            subject_id=subject.id,
            module_id=module.id,
            title=title,
            slug=slug,
            description=description,
        )
        self.save_block(subject, module, block)
        return block

    def save_block(self, subject: Subject, module: Module, block: StudyBlock) -> None:
        source_file = block.imported_files[0].original_path if block.imported_files else None
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
                    module.id,
                    block.slug,
                    block.title,
                    block.description,
                    source_file,
                    json.dumps([item.to_dict() for item in block.imported_files], ensure_ascii=False),
                    block.extracted_content.text,
                    block.generated_prompt,
                    block.ai_response_raw,
                    json.dumps(block.ai_response.to_dict(), ensure_ascii=False) if block.ai_response else None,
                    block.summary.content if block.summary else "",
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

    def list_blocks(self, subject_ref: str, module_ref: str) -> list[StudyBlock]:
        _, module = self.get_module(subject_ref, module_ref)
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM study_blocks WHERE module_id = ? ORDER BY created_at, title",
                (module.id,),
            ).fetchall()
        return [self._block_from_row(row) for row in rows]

    def get_block(
        self,
        subject_ref: str,
        module_ref: str,
        block_ref: str,
    ) -> tuple[Subject, Module, StudyBlock]:
        subject, module = self.get_module(subject_ref, module_ref)
        with self.connect() as db:
            row = db.execute(
                """
                SELECT * FROM study_blocks
                WHERE module_id = ?
                  AND (lower(id)=lower(?) OR lower(slug)=lower(?) OR lower(title)=lower(?))
                LIMIT 1
                """,
                (module.id, block_ref, block_ref, block_ref),
            ).fetchone()
        if row is None:
            raise ValueError(f"Bloco nao encontrado: {block_ref}")
        return subject, module, self._block_from_row(row)

    def get_block_by_id(self, block_id: str) -> tuple[Subject, Module, StudyBlock]:
        with self.connect() as db:
            row = db.execute(
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
        if row is None:
            raise ValueError(f"Bloco nao encontrado: {block_id}")
        subject = Subject(
            id=row["subject_id"],
            slug=row["subject_slug"],
            name=row["subject_name"],
            description=row["subject_description"],
            icon=row["subject_icon"],
            color=row["subject_color"],
            created_at=row["subject_created_at"],
            updated_at=row["subject_updated_at"],
        )
        module = Module(
            id=row["module_id"],
            subject_id=subject.id,
            slug=row["module_slug"],
            name=row["module_name"],
            description=row["module_description"],
            created_at=row["module_created_at"],
            updated_at=row["module_updated_at"],
        )
        return subject, module, self._block_from_row(row)

    def delete_block(self, subject_ref: str, module_ref: str, block_ref: str) -> None:
        subject, module, block = self.get_block(subject_ref, module_ref, block_ref)
        with self.connect() as db:
            db.execute("DELETE FROM study_blocks WHERE id = ?", (block.id,))
        shutil.rmtree(self.block_path(subject.slug, module.slug, block.slug), ignore_errors=True)

    def get_progress(self, block_id: str) -> StudyProgress:
        with self.connect() as db:
            row = db.execute("SELECT * FROM study_progress WHERE block_id = ?", (block_id,)).fetchone()
        if row is None:
            return StudyProgress()
        return StudyProgress.from_dict(
            {
                "flashcards_total": row["total_flashcards"],
                "flashcards_reviewed": row["reviewed_flashcards"],
                "questions_total": row["total_questions"],
                "questions_answered": row["answered_questions"],
                "questions_correct": row["correct_answers"],
                "reviewed_flashcards": json.loads(row["reviewed_flashcards_json"] or "{}"),
                "flashcard_reviews": json.loads(row["flashcard_reviews_json"] or "{}"),
                "answered_questions": json.loads(row["answered_questions_json"] or "{}"),
                "study_time_seconds": row["study_time_seconds"] or 0,
                "last_accessed_at": row["last_accessed_at"],
                "updated_at": row["updated_at"],
            }
        )

    def save_progress(self, block_id: str, progress: StudyProgress) -> StudyProgress:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO study_progress (
                    id, block_id, reviewed_flashcards, answered_questions, correct_answers,
                    total_flashcards, total_questions, progress_percent,
                    reviewed_flashcards_json, flashcard_reviews_json, answered_questions_json,
                    study_time_seconds, last_accessed_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    self._progress_percent(progress),
                    json.dumps(progress.reviewed_flashcards, ensure_ascii=False),
                    json.dumps(progress.flashcard_reviews, ensure_ascii=False),
                    json.dumps(progress.answered_questions, ensure_ascii=False),
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

    def database_stats(self) -> dict[str, int]:
        tables = ["subjects", "modules", "study_blocks", "flashcards", "questions", "study_progress"]
        with self.connect() as db:
            return {
                table: int(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in tables
            }

    def recent_records(self, limit: int = 12) -> list[dict[str, str]]:
        with self.connect() as db:
            rows = db.execute(
                """
                SELECT 'Materia' AS kind, name AS title, created_at FROM subjects
                UNION ALL
                SELECT 'Modulo' AS kind, name AS title, created_at FROM modules
                UNION ALL
                SELECT 'Bloco' AS kind, title, created_at FROM study_blocks
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def subject_path(self, subject_slug: str) -> Path:
        return self.files_path / subject_slug

    def modules_path(self, subject_slug: str) -> Path:
        return self.subject_path(subject_slug) / "modules"

    def module_path(self, subject_slug: str, module_slug: str) -> Path:
        return self.modules_path(subject_slug) / module_slug

    def blocks_path(self, subject_slug: str, module_slug: str) -> Path:
        return self.module_path(subject_slug, module_slug) / "blocks"

    def block_path(self, subject_slug: str, module_slug: str, block_slug: str) -> Path:
        return self.blocks_path(subject_slug, module_slug) / block_slug

    def make_unique_subject_slug(self, name: str) -> str:
        return self._make_unique_slug("subjects", None, name)

    def make_unique_module_slug(self, subject_id: str, name: str) -> str:
        return self._make_unique_slug("modules", subject_id, name)

    def make_unique_block_slug(self, module_id: str, title: str) -> str:
        return self._make_unique_slug("study_blocks", module_id, title)

    def _initialize(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS subjects (
                    id TEXT PRIMARY KEY,
                    slug TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    icon TEXT,
                    color TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS modules (
                    id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
                    slug TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(subject_id, slug)
                );
                CREATE TABLE IF NOT EXISTS study_blocks (
                    id TEXT PRIMARY KEY,
                    module_id TEXT NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
                    slug TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    source_file TEXT,
                    imported_files_json TEXT,
                    extracted_text TEXT,
                    generated_prompt TEXT,
                    ai_response_raw TEXT,
                    ai_response_json TEXT,
                    summary_text TEXT,
                    summary_visual TEXT,
                    preferred_summary_mode TEXT DEFAULT 'text',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(module_id, slug)
                );
                CREATE TABLE IF NOT EXISTS flashcards (
                    id TEXT PRIMARY KEY,
                    block_id TEXT NOT NULL REFERENCES study_blocks(id) ON DELETE CASCADE,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    source TEXT,
                    difficulty TEXT,
                    status TEXT DEFAULT 'new',
                    times_reviewed INTEGER DEFAULT 0,
                    last_reviewed_at TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS questions (
                    id TEXT PRIMARY KEY,
                    block_id TEXT NOT NULL REFERENCES study_blocks(id) ON DELETE CASCADE,
                    question_text TEXT NOT NULL,
                    option_a TEXT,
                    option_b TEXT,
                    option_c TEXT,
                    option_d TEXT,
                    correct_option TEXT,
                    explanation TEXT,
                    user_answer TEXT,
                    is_correct INTEGER,
                    answered_at TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS study_progress (
                    id TEXT PRIMARY KEY,
                    block_id TEXT UNIQUE NOT NULL REFERENCES study_blocks(id) ON DELETE CASCADE,
                    reviewed_flashcards INTEGER DEFAULT 0,
                    answered_questions INTEGER DEFAULT 0,
                    correct_answers INTEGER DEFAULT 0,
                    total_flashcards INTEGER DEFAULT 0,
                    total_questions INTEGER DEFAULT 0,
                    progress_percent INTEGER DEFAULT 0,
                    reviewed_flashcards_json TEXT DEFAULT '{}',
                    flashcard_reviews_json TEXT DEFAULT '{}',
                    answered_questions_json TEXT DEFAULT '{}',
                    study_time_seconds INTEGER DEFAULT 0,
                    last_accessed_at TEXT,
                    updated_at TEXT NOT NULL
                );
                """
            )
            self._ensure_column(db, "study_progress", "flashcard_reviews_json", "TEXT DEFAULT '{}'")

    def _migrate_json_if_empty(self) -> None:
        if self.database_stats()["subjects"] > 0:
            return
        json_subjects = self.subjects_path
        if not json_subjects.exists():
            return
        try:
            local = LocalStorage(self.base_path)
            for subject in local.list_subjects():
                self.save_subject(subject)
                for module in local.list_modules(subject.slug):
                    self.save_module(subject, module)
                    for block in local.list_blocks(subject.slug, module.slug):
                        self.save_block(subject, module, block)
        except Exception:
            return

    def _ensure_column(self, db: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        columns = [row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in columns:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def _make_unique_slug(self, table: str, parent_id: str | None, name: str) -> str:
        base = slugify(name)
        slug = base
        counter = 2
        with self.connect() as db:
            while True:
                if table == "subjects":
                    exists = db.execute("SELECT 1 FROM subjects WHERE slug = ?", (slug,)).fetchone()
                elif table == "modules":
                    exists = db.execute(
                        "SELECT 1 FROM modules WHERE subject_id = ? AND slug = ?",
                        (parent_id, slug),
                    ).fetchone()
                else:
                    exists = db.execute(
                        "SELECT 1 FROM study_blocks WHERE module_id = ? AND slug = ?",
                        (parent_id, slug),
                    ).fetchone()
                if exists is None:
                    return slug
                slug = f"{base}_{counter}"
                counter += 1

    def _subject_from_row(self, row: sqlite3.Row) -> Subject:
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
        with self.connect() as db:
            rows = db.execute(
                "SELECT slug FROM modules WHERE subject_id = ? ORDER BY created_at, name",
                (subject.id,),
            ).fetchall()
        subject.modules = [module_row["slug"] for module_row in rows]
        return subject

    def _module_from_row(self, row: sqlite3.Row) -> Module:
        module = Module(
            id=row["id"],
            subject_id=row["subject_id"],
            slug=row["slug"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        with self.connect() as db:
            rows = db.execute("SELECT slug FROM study_blocks WHERE module_id = ?", (module.id,)).fetchall()
        module.study_blocks = [row["slug"] for row in rows]
        return module

    def _block_from_row(self, row: sqlite3.Row) -> StudyBlock:
        imported_files = [
            ImportedFile.from_dict(item)
            for item in self._json_list(row["imported_files_json"])
            if isinstance(item, dict)
        ]
        ai_response = AIResponse.from_dict(self._json_dict(row["ai_response_json"]))
        block = StudyBlock(
            id=row["id"],
            subject_id=self._subject_id_for_module(row["module_id"]),
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
            ai_response=ai_response,
            summary=Summary(row["summary_text"]) if row["summary_text"] else None,
            summary_visual=row["summary_visual"] or "",
            preferred_summary_mode=row["preferred_summary_mode"] or "text",
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        block.flashcards = self._flashcards_for_block(block.id)
        block.questions = self._questions_for_block(block.id)
        return block

    def _subject_id_for_module(self, module_id: str) -> str:
        with self.connect() as db:
            row = db.execute("SELECT subject_id FROM modules WHERE id = ?", (module_id,)).fetchone()
        return str(row["subject_id"]) if row else ""

    def _flashcards_for_block(self, block_id: str) -> list[Flashcard]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM flashcards WHERE block_id = ? ORDER BY created_at", (block_id,)).fetchall()
        return [
            Flashcard(id=row["id"], question=row["question"], answer=row["answer"], source=row["source"])
            for row in rows
        ]

    def _questions_for_block(self, block_id: str) -> list[Question]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM questions WHERE block_id = ? ORDER BY created_at", (block_id,)).fetchall()
        return [
            Question(
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
            for row in rows
        ]

    def _json_list(self, raw: str | None) -> list[Any]:
        try:
            value = json.loads(raw or "[]")
            return value if isinstance(value, list) else []
        except json.JSONDecodeError:
            return []

    def _json_dict(self, raw: str | None) -> dict[str, Any] | None:
        try:
            value = json.loads(raw or "null")
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            return None

    def _progress_percent(self, progress: StudyProgress) -> int:
        total = progress.flashcards_total + progress.questions_total
        done = progress.flashcards_reviewed + progress.questions_answered
        return int((done / total) * 100) if total else 0
