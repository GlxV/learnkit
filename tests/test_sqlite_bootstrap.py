from __future__ import annotations

from pathlib import Path

from app.infrastructure.sqlite.bootstrap import SQLiteBootstrap
from app.infrastructure.sqlite.connection import connect_sqlite


def test_sqlite_bootstrap_initializes_schema_and_legacy_columns(tmp_path: Path) -> None:
    db_path = tmp_path / "learnkit.db"

    def connect():
        return connect_sqlite(db_path)

    with connect() as db:
        db.execute(
            """
            CREATE TABLE study_progress (
                id TEXT PRIMARY KEY,
                block_id TEXT UNIQUE NOT NULL,
                reviewed_flashcards INTEGER DEFAULT 0,
                answered_questions INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                total_flashcards INTEGER DEFAULT 0,
                total_questions INTEGER DEFAULT 0,
                progress_percent INTEGER DEFAULT 0,
                reviewed_flashcards_json TEXT DEFAULT '{}',
                answered_questions_json TEXT DEFAULT '{}',
                study_time_seconds INTEGER DEFAULT 0,
                last_accessed_at TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )

    SQLiteBootstrap(connect).initialize()

    with connect() as db:
        progress_columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(study_progress)").fetchall()
        }
        migrations_table = db.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'schema_migrations'
            """
        ).fetchone()
        migration_versions = {
            row["version"]
            for row in db.execute("SELECT version FROM schema_migrations").fetchall()
        }

    assert "flashcard_reviews_json" in progress_columns
    assert "question_attempts_json" in progress_columns
    assert migrations_table is not None
    assert 1 in migration_versions
