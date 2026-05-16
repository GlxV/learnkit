from __future__ import annotations

import sqlite3
from typing import Callable


class DashboardQueries:
    def __init__(self, connect: Callable[[], sqlite3.Connection]) -> None:
        self.connect = connect

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

