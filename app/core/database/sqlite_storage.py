from __future__ import annotations

import sqlite3
import shutil
from pathlib import Path

from app.core.models.module import Module
from app.core.models.progress import StudyProgress
from app.core.models.review_schedule import ReviewSchedule
from app.core.models.study_block import StudyBlock
from app.core.models.subject import Subject
from app.core.storage.local_storage import slugify
from app.infrastructure.sqlite.bootstrap import SQLiteBootstrap
from app.infrastructure.sqlite.connection import connect_sqlite
from app.infrastructure.sqlite.queries.dashboard_queries import DashboardQueries
from app.infrastructure.sqlite.repositories.block_repository import BlockRepository
from app.infrastructure.sqlite.repositories.module_repository import ModuleRepository
from app.infrastructure.sqlite.repositories.progress_repository import ProgressRepository
from app.infrastructure.sqlite.repositories.review_schedule_repository import ReviewScheduleRepository
from app.infrastructure.sqlite.repositories.subject_repository import SubjectRepository


class SQLiteStorage:
    def __init__(self, db_path: str | Path = "data/learnkit.db", migrate_json: bool = True) -> None:
        self.db_path = Path(db_path)
        self.base_path = self.db_path.parent
        self.subjects_path = self.base_path / "subjects"
        self.files_path = self.base_path / "sqlite_files"
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.files_path.mkdir(parents=True, exist_ok=True)
        self.dashboard_queries = DashboardQueries(self.connect)
        self.subject_repository = SubjectRepository(self.connect)
        self.module_repository = ModuleRepository(self.connect)
        self.block_repository = BlockRepository(self.connect)
        self.progress_repository = ProgressRepository(self.connect)
        self.review_schedule_repository = ReviewScheduleRepository(self.connect)
        self.bootstrap = SQLiteBootstrap(self.connect)
        self.bootstrap.initialize()
        if migrate_json:
            self.bootstrap.migrate_json_if_empty(
                base_path=self.base_path,
                subjects_path=self.subjects_path,
                database_stats=self.database_stats,
                save_subject=self.save_subject,
                save_module=self.save_module,
                save_block=self.save_block,
            )

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.db_path)

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
        self.subject_repository.save(subject)

    def list_subjects(self) -> list[Subject]:
        return self.subject_repository.list_subjects()

    def get_subject(self, subject_ref: str) -> Subject:
        subject = self.subject_repository.get_subject(subject_ref)
        if subject is None:
            raise ValueError(f"Materia nao encontrada: {subject_ref}")
        return subject

    def delete_subject(self, subject_ref: str) -> None:
        subject = self.get_subject(subject_ref)
        self.subject_repository.delete(subject.id)
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
        self.module_repository.save(subject, module)

    def list_modules(self, subject_ref: str) -> list[Module]:
        subject = self.get_subject(subject_ref)
        return self.module_repository.list_modules(subject.id)

    def get_module(self, subject_ref: str, module_ref: str) -> tuple[Subject, Module]:
        subject = self.get_subject(subject_ref)
        module = self.module_repository.get_module(subject.id, module_ref)
        if module is None:
            raise ValueError(f"Modulo nao encontrado: {module_ref}")
        return subject, module

    def delete_module(self, subject_ref: str, module_ref: str) -> None:
        subject, module = self.get_module(subject_ref, module_ref)
        self.module_repository.delete(module.id)
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
        self.block_repository.save(block, module.id)

    def list_blocks(self, subject_ref: str, module_ref: str) -> list[StudyBlock]:
        subject, module = self.get_module(subject_ref, module_ref)
        return self.block_repository.list_blocks(module.id, subject.id)

    def get_block(
        self,
        subject_ref: str,
        module_ref: str,
        block_ref: str,
    ) -> tuple[Subject, Module, StudyBlock]:
        subject, module = self.get_module(subject_ref, module_ref)
        block = self.block_repository.get_block(module.id, block_ref, subject.id)
        if block is None:
            raise ValueError(f"Bloco nao encontrado: {block_ref}")
        return subject, module, block

    def get_block_by_id(self, block_id: str) -> tuple[Subject, Module, StudyBlock]:
        context = self.block_repository.get_block_context(block_id)
        if context is None:
            raise ValueError(f"Bloco nao encontrado: {block_id}")
        return context

    def delete_block(self, subject_ref: str, module_ref: str, block_ref: str) -> None:
        subject, module, block = self.get_block(subject_ref, module_ref, block_ref)
        self.block_repository.delete(block.id)
        shutil.rmtree(self.block_path(subject.slug, module.slug, block.slug), ignore_errors=True)

    def get_progress(self, block_id: str) -> StudyProgress:
        return self.progress_repository.get_progress(block_id)

    def save_progress(self, block_id: str, progress: StudyProgress) -> StudyProgress:
        return self.progress_repository.save(block_id, progress)

    def create_review_schedules(self, schedules: list[ReviewSchedule]) -> list[ReviewSchedule]:
        return self.review_schedule_repository.create_many(schedules)

    def list_review_schedules(self, block_id: str) -> list[ReviewSchedule]:
        return self.review_schedule_repository.list_for_block(block_id)

    def list_pending_review_schedules(self) -> list[ReviewSchedule]:
        return self.review_schedule_repository.list_by_status("pending")

    def get_review_schedule(self, schedule_id: str) -> ReviewSchedule:
        schedule = self.review_schedule_repository.get(schedule_id)
        if schedule is None:
            raise ValueError(f"Revisao nao encontrada: {schedule_id}")
        return schedule

    def update_review_schedule_status(
        self,
        schedule_id: str,
        status: str,
        completed_at: str,
    ) -> ReviewSchedule:
        return self.review_schedule_repository.update_status(schedule_id, status, completed_at)

    def database_stats(self) -> dict[str, int]:
        return self.dashboard_queries.database_stats()

    def recent_records(self, limit: int = 12) -> list[dict[str, str]]:
        return self.dashboard_queries.recent_records(limit)

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

    def _make_unique_slug(self, table: str, parent_id: str | None, name: str) -> str:
        base = slugify(name)
        slug = base
        counter = 2
        while True:
            if table == "subjects":
                exists = self.subject_repository.slug_exists(slug)
            elif table == "modules":
                exists = self.module_repository.slug_exists(str(parent_id or ""), slug)
            else:
                exists = self.block_repository.slug_exists(str(parent_id or ""), slug)
            if not exists:
                return slug
            slug = f"{base}_{counter}"
            counter += 1
