from __future__ import annotations

import json
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any

from app.core.models.module import Module
from app.core.models.study_block import StudyBlock
from app.core.models.subject import Subject


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_value.lower()).strip("_")
    return slug or "item"


class LocalStorage:
    def __init__(self, base_path: str | Path = "data") -> None:
        self.base_path = Path(base_path)
        self.subjects_path = self.base_path / "subjects"
        self.subjects_path.mkdir(parents=True, exist_ok=True)

    def make_unique_slug(self, parent_path: Path, desired_name: str) -> str:
        base_slug = slugify(desired_name)
        slug = base_slug
        counter = 2
        while (parent_path / slug).exists():
            slug = f"{base_slug}_{counter}"
            counter += 1
        return slug

    def create_subject(
        self,
        name: str,
        description: str | None = None,
        icon: str | None = None,
        color: str | None = None,
    ) -> Subject:
        slug = self.make_unique_slug(self.subjects_path, name)
        subject = Subject(name=name, slug=slug, description=description, icon=icon, color=color)
        self.save_subject(subject)
        return subject

    def save_subject(self, subject: Subject) -> None:
        path = self.subject_path(subject.slug)
        path.mkdir(parents=True, exist_ok=True)
        self._write_json(path / "subject.json", subject.to_dict())

    def list_subjects(self) -> list[Subject]:
        subjects: list[Subject] = []
        for subject_dir in sorted(self.subjects_path.iterdir()):
            subject_file = subject_dir / "subject.json"
            if subject_file.exists():
                subjects.append(Subject.from_dict(self._read_json(subject_file)))
        return subjects

    def get_subject(self, subject_ref: str) -> Subject:
        for subject in self.list_subjects():
            if self._matches(subject_ref, subject.id, subject.slug, subject.name):
                return subject
        raise ValueError(f"Materia nao encontrada: {subject_ref}")

    def delete_subject(self, subject_ref: str) -> None:
        subject = self.get_subject(subject_ref)
        shutil.rmtree(self.subject_path(subject.slug))

    def save_module(self, subject: Subject, module: Module) -> None:
        path = self.module_path(subject.slug, module.slug)
        path.mkdir(parents=True, exist_ok=True)
        self._write_json(path / "module.json", module.to_dict())

    def create_module(
        self,
        subject_ref: str,
        name: str,
        description: str | None = None,
    ) -> Module:
        subject = self.get_subject(subject_ref)
        modules_path = self.modules_path(subject.slug)
        modules_path.mkdir(parents=True, exist_ok=True)
        slug = self.make_unique_slug(modules_path, name)
        module = Module(
            subject_id=subject.id,
            name=name,
            slug=slug,
            description=description,
        )
        self.save_module(subject, module)
        subject.modules.append(module.slug)
        subject.touch()
        self.save_subject(subject)
        return module

    def list_modules(self, subject_ref: str) -> list[Module]:
        subject = self.get_subject(subject_ref)
        modules_path = self.modules_path(subject.slug)
        if not modules_path.exists():
            return []

        modules: list[Module] = []
        for module_dir in sorted(modules_path.iterdir()):
            module_file = module_dir / "module.json"
            if module_file.exists():
                modules.append(Module.from_dict(self._read_json(module_file)))
        return modules

    def get_module(self, subject_ref: str, module_ref: str) -> tuple[Subject, Module]:
        subject = self.get_subject(subject_ref)
        for module in self.list_modules(subject.slug):
            if self._matches(module_ref, module.id, module.slug, module.name):
                return subject, module
        raise ValueError(f"Modulo nao encontrado: {module_ref}")

    def delete_module(self, subject_ref: str, module_ref: str) -> None:
        subject, module = self.get_module(subject_ref, module_ref)
        shutil.rmtree(self.module_path(subject.slug, module.slug))
        subject.modules = [slug for slug in subject.modules if slug != module.slug]
        subject.touch()
        self.save_subject(subject)

    def save_block(self, subject: Subject, module: Module, block: StudyBlock) -> None:
        path = self.block_path(subject.slug, module.slug, block.slug)
        path.mkdir(parents=True, exist_ok=True)
        self._write_json(path / "block.json", block.to_dict())

        if block.extracted_content.text:
            (path / "extracted_text.md").write_text(block.extracted_content.text, encoding="utf-8")
        if block.generated_prompt:
            (path / "generated_prompt.md").write_text(block.generated_prompt, encoding="utf-8")
        if block.ai_response_raw:
            (path / "ai_response.md").write_text(block.ai_response_raw, encoding="utf-8")
        if block.summary:
            (path / "summary.md").write_text(block.summary.content, encoding="utf-8")
        if block.flashcards:
            self._write_json(
                path / "flashcards.json",
                [flashcard.to_dict() for flashcard in block.flashcards],
            )
        if block.questions:
            self._write_json(
                path / "questions.json",
                [question.to_dict() for question in block.questions],
            )

    def create_block(
        self,
        subject_ref: str,
        module_ref: str,
        title: str,
        description: str | None = None,
    ) -> StudyBlock:
        subject, module = self.get_module(subject_ref, module_ref)
        blocks_path = self.blocks_path(subject.slug, module.slug)
        blocks_path.mkdir(parents=True, exist_ok=True)
        slug = self.make_unique_slug(blocks_path, title)
        block = StudyBlock(
            subject_id=subject.id,
            module_id=module.id,
            title=title,
            slug=slug,
            description=description,
        )
        self.save_block(subject, module, block)
        module.study_blocks.append(block.slug)
        module.touch()
        self.save_module(subject, module)
        return block

    def list_blocks(self, subject_ref: str, module_ref: str) -> list[StudyBlock]:
        subject, module = self.get_module(subject_ref, module_ref)
        blocks_path = self.blocks_path(subject.slug, module.slug)
        if not blocks_path.exists():
            return []

        blocks: list[StudyBlock] = []
        for block_dir in sorted(blocks_path.iterdir()):
            block_file = block_dir / "block.json"
            if block_file.exists():
                blocks.append(StudyBlock.from_dict(self._read_json(block_file)))
        return blocks

    def get_block(
        self,
        subject_ref: str,
        module_ref: str,
        block_ref: str,
    ) -> tuple[Subject, Module, StudyBlock]:
        subject, module = self.get_module(subject_ref, module_ref)
        for block in self.list_blocks(subject.slug, module.slug):
            if self._matches(block_ref, block.id, block.slug, block.title):
                return subject, module, block
        raise ValueError(f"Bloco nao encontrado: {block_ref}")

    def get_block_by_id(self, block_id: str) -> tuple[Subject, Module, StudyBlock]:
        for subject in self.list_subjects():
            for module in self.list_modules(subject.slug):
                for block in self.list_blocks(subject.slug, module.slug):
                    if block.id == block_id:
                        return subject, module, block
        raise ValueError(f"Bloco nao encontrado: {block_id}")

    def delete_block(self, subject_ref: str, module_ref: str, block_ref: str) -> None:
        subject, module, block = self.get_block(subject_ref, module_ref, block_ref)
        shutil.rmtree(self.block_path(subject.slug, module.slug, block.slug))
        module.study_blocks = [slug for slug in module.study_blocks if slug != block.slug]
        module.touch()
        self.save_module(subject, module)

    def subject_path(self, subject_slug: str) -> Path:
        return self.subjects_path / subject_slug

    def modules_path(self, subject_slug: str) -> Path:
        return self.subject_path(subject_slug) / "modules"

    def module_path(self, subject_slug: str, module_slug: str) -> Path:
        return self.modules_path(subject_slug) / module_slug

    def blocks_path(self, subject_slug: str, module_slug: str) -> Path:
        return self.module_path(subject_slug, module_slug) / "blocks"

    def block_path(self, subject_slug: str, module_slug: str, block_slug: str) -> Path:
        return self.blocks_path(subject_slug, module_slug) / block_slug

    def _read_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _matches(self, query: str, item_id: str, slug: str, name: str) -> bool:
        normalized = query.casefold()
        return normalized in {item_id.casefold(), slug.casefold(), name.casefold()}
