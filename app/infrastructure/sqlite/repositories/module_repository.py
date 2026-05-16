from __future__ import annotations

import sqlite3
from typing import Callable

from app.core.models.module import Module
from app.core.models.subject import Subject
from app.infrastructure.sqlite.row_mappers import module_from_row


class ModuleRepository:
    def __init__(self, connect: Callable[[], sqlite3.Connection]) -> None:
        self.connect = connect

    def list_rows(self, subject_id: str) -> list[sqlite3.Row]:
        with self.connect() as db:
            return db.execute(
                "SELECT * FROM modules WHERE subject_id = ? ORDER BY created_at, name",
                (subject_id,),
            ).fetchall()

    def list_modules(self, subject_id: str) -> list[Module]:
        return [module_from_row(row, self.block_slugs(row["id"])) for row in self.list_rows(subject_id)]

    def get_row(self, subject_id: str, module_ref: str) -> sqlite3.Row | None:
        with self.connect() as db:
            return db.execute(
                """
                SELECT * FROM modules
                WHERE subject_id = ?
                  AND (lower(id)=lower(?) OR lower(slug)=lower(?) OR lower(name)=lower(?))
                LIMIT 1
                """,
                (subject_id, module_ref, module_ref, module_ref),
            ).fetchone()

    def get_module(self, subject_id: str, module_ref: str) -> Module | None:
        row = self.get_row(subject_id, module_ref)
        if row is None:
            return None
        return module_from_row(row, self.block_slugs(row["id"]))

    def save(self, subject: Subject, module: Module) -> None:
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

    def delete(self, module_id: str) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM modules WHERE id = ?", (module_id,))

    def block_slugs(self, module_id: str) -> list[str]:
        with self.connect() as db:
            rows = db.execute("SELECT slug FROM study_blocks WHERE module_id = ?", (module_id,)).fetchall()
        return [row["slug"] for row in rows]

    def slug_exists(self, subject_id: str, slug: str) -> bool:
        with self.connect() as db:
            return (
                db.execute(
                    "SELECT 1 FROM modules WHERE subject_id = ? AND slug = ?",
                    (subject_id, slug),
                ).fetchone()
                is not None
            )
