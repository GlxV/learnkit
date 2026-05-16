from __future__ import annotations

import sqlite3
from typing import Callable

from app.core.models.subject import Subject
from app.infrastructure.sqlite.row_mappers import subject_from_row


class SubjectRepository:
    def __init__(self, connect: Callable[[], sqlite3.Connection]) -> None:
        self.connect = connect

    def list_rows(self) -> list[sqlite3.Row]:
        with self.connect() as db:
            return db.execute("SELECT * FROM subjects ORDER BY created_at, name").fetchall()

    def list_subjects(self) -> list[Subject]:
        return [subject_from_row(row, self.module_slugs(row["id"])) for row in self.list_rows()]

    def get_row(self, subject_ref: str) -> sqlite3.Row | None:
        with self.connect() as db:
            return db.execute(
                """
                SELECT * FROM subjects
                WHERE lower(id)=lower(?) OR lower(slug)=lower(?) OR lower(name)=lower(?)
                LIMIT 1
                """,
                (subject_ref, subject_ref, subject_ref),
            ).fetchone()

    def get_subject(self, subject_ref: str) -> Subject | None:
        row = self.get_row(subject_ref)
        if row is None:
            return None
        return subject_from_row(row, self.module_slugs(row["id"]))

    def save(self, subject: Subject) -> None:
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

    def delete(self, subject_id: str) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))

    def module_slugs(self, subject_id: str) -> list[str]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT slug FROM modules WHERE subject_id = ? ORDER BY created_at, name",
                (subject_id,),
            ).fetchall()
        return [row["slug"] for row in rows]

    def slug_exists(self, slug: str) -> bool:
        with self.connect() as db:
            return db.execute("SELECT 1 FROM subjects WHERE slug = ?", (slug,)).fetchone() is not None
