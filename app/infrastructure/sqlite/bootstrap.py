from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Callable

from app.core.models.module import Module
from app.core.models.study_block import StudyBlock
from app.core.models.subject import Subject
from app.core.storage.local_storage import LocalStorage
from app.infrastructure.sqlite.migrations import DEFAULT_MIGRATIONS, MigrationRunner, SCHEMA_SQL


class SQLiteBootstrap:
    def __init__(self, connect: Callable[[], sqlite3.Connection]) -> None:
        self.connect = connect

    def initialize(self) -> None:
        with self.connect() as db:
            db.executescript(SCHEMA_SQL)
        MigrationRunner(self.connect, DEFAULT_MIGRATIONS).apply_pending()

    def migrate_json_if_empty(
        self,
        *,
        base_path: Path,
        subjects_path: Path,
        database_stats: Callable[[], dict[str, int]],
        save_subject: Callable[[Subject], None],
        save_module: Callable[[Subject, Module], None],
        save_block: Callable[[Subject, Module, StudyBlock], None],
    ) -> None:
        if database_stats()["subjects"] > 0:
            return
        if not subjects_path.exists():
            return
        try:
            local = LocalStorage(base_path)
            for subject in local.list_subjects():
                save_subject(subject)
                for module in local.list_modules(subject.slug):
                    save_module(subject, module)
                    for block in local.list_blocks(subject.slug, module.slug):
                        save_block(subject, module, block)
        except Exception:
            return
