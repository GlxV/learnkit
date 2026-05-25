from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Callable

from app.core.models.base import utc_now


REVIEW_SCHEDULES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS review_schedules (
    id TEXT PRIMARY KEY,
    study_block_id TEXT NOT NULL REFERENCES study_blocks(id) ON DELETE CASCADE,
    subject_id TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    module_id TEXT NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    review_step TEXT NOT NULL CHECK(review_step IN ('1h', '24h', '7d', '30d')),
    scheduled_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'done', 'skipped')),
    created_at TEXT NOT NULL,
    UNIQUE(study_block_id, review_step)
);
"""

REVIEW_SCHEDULES_STATUS_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_review_schedules_status_scheduled
ON review_schedules(status, scheduled_at);
"""

REVIEW_SCHEDULES_BLOCK_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_review_schedules_block
ON review_schedules(study_block_id);
"""


SCHEMA_SQL = """
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
    question_attempts_json TEXT DEFAULT '{}',
    study_time_seconds INTEGER DEFAULT 0,
    last_accessed_at TEXT,
    updated_at TEXT NOT NULL
);
""" + REVIEW_SCHEDULES_TABLE_SQL + REVIEW_SCHEDULES_STATUS_INDEX_SQL + REVIEW_SCHEDULES_BLOCK_INDEX_SQL


SCHEMA_MIGRATIONS_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL
);
"""


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    name: str
    statements: tuple[str, ...]
    operation: Callable[[sqlite3.Connection], None] | None = None


def _ensure_column(db: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = [row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in columns:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _add_progress_review_json_columns(db: sqlite3.Connection) -> None:
    _ensure_column(db, "study_progress", "flashcard_reviews_json", "TEXT DEFAULT '{}'")
    _ensure_column(db, "study_progress", "question_attempts_json", "TEXT DEFAULT '{}'")


DEFAULT_MIGRATIONS = (
    Migration(
        version=1,
        name="add_progress_review_json_columns",
        statements=(),
        operation=_add_progress_review_json_columns,
    ),
    Migration(
        version=2,
        name="add_review_schedules_table",
        statements=(
            REVIEW_SCHEDULES_TABLE_SQL,
            REVIEW_SCHEDULES_STATUS_INDEX_SQL,
            REVIEW_SCHEDULES_BLOCK_INDEX_SQL,
        ),
    ),
)


class MigrationRunner:
    def __init__(
        self,
        connect: Callable[[], sqlite3.Connection],
        migrations: list[Migration] | tuple[Migration, ...] | None = None,
    ) -> None:
        self.connect = connect
        self.migrations = sorted(migrations or [], key=lambda migration: migration.version)

    def ensure_schema_table(self) -> None:
        with self.connect() as db:
            db.executescript(SCHEMA_MIGRATIONS_SQL)

    def applied_versions(self) -> set[int]:
        self.ensure_schema_table()
        with self.connect() as db:
            rows = db.execute("SELECT version FROM schema_migrations").fetchall()
        return {int(row["version"]) for row in rows}

    def apply_pending(self) -> list[int]:
        self.ensure_schema_table()
        applied = self.applied_versions()
        applied_now: list[int] = []
        with self.connect() as db:
            for migration in self.migrations:
                if migration.version in applied:
                    continue
                for statement in migration.statements:
                    db.execute(statement)
                if migration.operation is not None:
                    migration.operation(db)
                db.execute(
                    """
                    INSERT INTO schema_migrations (version, name, applied_at)
                    VALUES (?, ?, ?)
                    """,
                    (migration.version, migration.name, utc_now()),
                )
                applied_now.append(migration.version)
        return applied_now
