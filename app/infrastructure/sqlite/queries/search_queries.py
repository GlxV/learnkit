from __future__ import annotations

import sqlite3
from typing import Callable


class SearchQueries:
    def __init__(self, connect: Callable[[], sqlite3.Connection]) -> None:
        self.connect = connect

    def block_hits(self, query: str, limit: int = 50) -> list[dict[str, str]]:
        like = f"%{query}%"
        with self.connect() as db:
            rows = db.execute(
                """
                SELECT
                    study_blocks.id AS block_id,
                    study_blocks.title AS block_title,
                    modules.name AS module_name,
                    subjects.name AS subject_name
                FROM study_blocks
                JOIN modules ON modules.id = study_blocks.module_id
                JOIN subjects ON subjects.id = modules.subject_id
                WHERE study_blocks.title LIKE ? OR study_blocks.summary_text LIKE ?
                ORDER BY study_blocks.updated_at DESC
                LIMIT ?
                """,
                (like, like, limit),
            ).fetchall()
        return [dict(row) for row in rows]

