from __future__ import annotations

import sqlite3
from typing import Callable

from app.core.models.review_schedule import ReviewSchedule
from app.infrastructure.sqlite.row_mappers import review_schedule_from_row


class ReviewScheduleRepository:
    VALID_STATUSES = {"pending", "done", "skipped"}

    def __init__(self, connect: Callable[[], sqlite3.Connection]) -> None:
        self.connect = connect

    def create_many(self, schedules: list[ReviewSchedule]) -> list[ReviewSchedule]:
        if not schedules:
            return []
        with self.connect() as db:
            db.executemany(
                """
                INSERT INTO review_schedules (
                    id, study_block_id, subject_id, module_id, review_step,
                    scheduled_at, completed_at, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(study_block_id, review_step) DO NOTHING
                """,
                [
                    (
                        item.id,
                        item.study_block_id,
                        item.subject_id,
                        item.module_id,
                        item.review_step,
                        item.scheduled_at,
                        item.completed_at,
                        item.status,
                        item.created_at,
                    )
                    for item in schedules
                ],
            )
        return self.list_for_block(schedules[0].study_block_id)

    def list_for_block(self, block_id: str) -> list[ReviewSchedule]:
        with self.connect() as db:
            rows = db.execute(
                """
                SELECT * FROM review_schedules
                WHERE study_block_id = ?
                ORDER BY scheduled_at, created_at
                """,
                (block_id,),
            ).fetchall()
        return [review_schedule_from_row(row) for row in rows]

    def list_by_status(self, status: str = "pending") -> list[ReviewSchedule]:
        if status not in self.VALID_STATUSES:
            raise ValueError("Status de revisao invalido.")
        with self.connect() as db:
            rows = db.execute(
                """
                SELECT * FROM review_schedules
                WHERE status = ?
                ORDER BY scheduled_at, created_at
                """,
                (status,),
            ).fetchall()
        return [review_schedule_from_row(row) for row in rows]

    def get(self, schedule_id: str) -> ReviewSchedule | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM review_schedules WHERE id = ? LIMIT 1",
                (schedule_id,),
            ).fetchone()
        return review_schedule_from_row(row) if row is not None else None

    def update_status(
        self,
        schedule_id: str,
        status: str,
        completed_at: str,
    ) -> ReviewSchedule:
        if status not in {"done", "skipped"}:
            raise ValueError("Status final de revisao invalido.")
        with self.connect() as db:
            db.execute(
                """
                UPDATE review_schedules
                SET status = ?, completed_at = ?
                WHERE id = ? AND status = 'pending'
                """,
                (status, completed_at, schedule_id),
            )
        stored = self.get(schedule_id)
        if stored is None:
            raise ValueError("Revisao nao encontrada.")
        return stored
