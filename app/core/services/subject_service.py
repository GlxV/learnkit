from __future__ import annotations

from app.core.models.subject import Subject
from app.core.storage.local_storage import LocalStorage


class SubjectService:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage

    def create_subject(
        self,
        name: str,
        description: str | None = None,
        icon: str | None = None,
        color: str | None = None,
    ) -> Subject:
        self._validate_name(name, "materia")
        return self.storage.create_subject(name.strip(), description, icon, color)

    def list_subjects(self) -> list[Subject]:
        return self.storage.list_subjects()

    def rename_subject(self, subject_ref: str, new_name: str) -> Subject:
        self._validate_name(new_name, "materia")
        subject = self.storage.get_subject(subject_ref)
        subject.name = new_name.strip()
        subject.touch()
        self.storage.save_subject(subject)
        return subject

    def update_subject(
        self,
        subject_ref: str,
        name: str,
        description: str | None = None,
        icon: str | None = None,
        color: str | None = None,
    ) -> Subject:
        self._validate_name(name, "materia")
        subject = self.storage.get_subject(subject_ref)
        subject.name = name.strip()
        subject.description = description
        subject.icon = icon
        subject.color = color
        subject.touch()
        self.storage.save_subject(subject)
        return subject

    def delete_subject(self, subject_ref: str) -> None:
        self.storage.delete_subject(subject_ref)

    def _validate_name(self, value: str, label: str) -> None:
        if not value or not value.strip():
            raise ValueError(f"O nome da {label} nao pode ficar vazio.")
