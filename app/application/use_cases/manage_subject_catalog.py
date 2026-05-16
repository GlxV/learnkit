from __future__ import annotations

from app.core.models.module import Module
from app.core.models.study_block import StudyBlock
from app.core.models.subject import Subject
from app.core.services.block_service import BlockService
from app.core.services.module_service import ModuleService
from app.core.services.subject_service import SubjectService
from app.core.storage.local_storage import LocalStorage


class ManageSubjectCatalogUseCase:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage
        self.subject_service = SubjectService(storage)
        self.module_service = ModuleService(storage)
        self.block_service = BlockService(storage)

    def create_subject(
        self,
        name: str,
        description: str | None = None,
        color: str | None = None,
        icon: str | None = None,
        initial_modules: list[str] | None = None,
    ) -> Subject:
        subject = self.subject_service.create_subject(name, description, icon=icon, color=color)
        for module_name in initial_modules or []:
            self.module_service.create_module(subject.slug, module_name)
        return subject

    def update_subject(
        self,
        subject_ref: str,
        name: str,
        description: str | None = None,
        color: str | None = None,
        icon: str | None = None,
    ) -> Subject:
        return self.subject_service.update_subject(
            subject_ref,
            name,
            description,
            icon=icon,
            color=color,
        )

    def create_module(
        self,
        subject_name: str,
        module_name: str,
        description: str | None = None,
    ) -> Module:
        try:
            self.storage.get_subject(subject_name)
        except ValueError:
            self.subject_service.create_subject(subject_name)
        return self.module_service.create_module(subject_name, module_name, description)

    def delete_subject(self, subject_ref: str) -> None:
        self.subject_service.delete_subject(subject_ref)

    def delete_module(self, subject_ref: str, module_ref: str) -> None:
        self.module_service.delete_module(subject_ref, module_ref)

    def delete_block(self, subject_ref: str, module_ref: str, block_ref: str) -> None:
        self.block_service.delete_block(subject_ref, module_ref, block_ref)

    def create_block(
        self,
        subject_ref: str,
        module_ref: str,
        title: str,
        description: str | None = None,
    ) -> StudyBlock:
        return self.block_service.create_block(subject_ref, module_ref, title, description=description)
