from __future__ import annotations

from app.core.models.module import Module
from app.core.storage.local_storage import LocalStorage


class ModuleService:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage

    def create_module(
        self,
        subject_ref: str,
        name: str,
        description: str | None = None,
    ) -> Module:
        self._validate_name(name)
        return self.storage.create_module(subject_ref, name.strip(), description)

    def list_modules(self, subject_ref: str) -> list[Module]:
        return self.storage.list_modules(subject_ref)

    def rename_module(self, subject_ref: str, module_ref: str, new_name: str) -> Module:
        self._validate_name(new_name)
        subject, module = self.storage.get_module(subject_ref, module_ref)
        module.name = new_name.strip()
        module.touch()
        self.storage.save_module(subject, module)
        return module

    def delete_module(self, subject_ref: str, module_ref: str) -> None:
        self.storage.delete_module(subject_ref, module_ref)

    def _validate_name(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("O nome do modulo nao pode ficar vazio.")
