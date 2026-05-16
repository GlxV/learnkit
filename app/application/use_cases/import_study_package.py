from __future__ import annotations

from app.application.dto.study_package import (
    ImportStudyPackageResultDTO,
    StudyPackageImportDTO,
)
from app.core.models.ai_response import AIResponse
from app.core.models.flashcard import Flashcard
from app.core.models.question import Question
from app.core.models.summary import Summary
from app.core.services.progress_service import ProgressService
from app.core.storage.local_storage import LocalStorage


class ImportStudyPackageUseCase:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage

    def execute(self, request: StudyPackageImportDTO) -> ImportStudyPackageResultDTO:
        mode = request.mode.strip().lower()
        if mode not in {"create", "update"}:
            raise ValueError("Modo de importacao invalido.")
        if not request.extraction.combined_content.text.strip():
            raise ValueError("Conteudo extraido vazio.")
        if not request.generated_prompt.strip():
            raise ValueError("Prompt gerado vazio.")
        if not request.package.has_content():
            raise ValueError("Pacote de estudo sem conteudo reconhecivel.")

        if mode == "update":
            return self._update(request)
        return self._create(request)

    def _create(self, request: StudyPackageImportDTO) -> ImportStudyPackageResultDTO:
        destination = request.destination
        subject_name = destination.subject_name.strip()
        module_name = destination.module_name.strip()
        block_title = destination.block_title.strip()
        if not subject_name or not module_name or not block_title:
            raise ValueError("Materia, modulo e bloco sao obrigatorios para criar.")

        created_subject = False
        created_module = False
        try:
            subject = self.storage.get_subject(subject_name)
        except ValueError:
            subject = self.storage.create_subject(subject_name)
            created_subject = True

        try:
            _, module = self.storage.get_module(subject.slug, module_name)
        except ValueError:
            module = self.storage.create_module(subject.slug, module_name)
            created_module = True

        block = self.storage.create_block(
            subject.slug,
            module.slug,
            block_title,
            destination.description,
        )
        subject, module, block = self.storage.get_block_by_id(block.id)
        block = self._fill_block(block, request)
        self.storage.save_block(subject, module, block)
        self._sync_progress(block.id)
        _, _, block = self.storage.get_block_by_id(block.id)
        return ImportStudyPackageResultDTO(
            block=block,
            subject_name=subject.name,
            module_name=module.name,
            created_subject=created_subject,
            created_module=created_module,
            mode="create",
        )

    def _update(self, request: StudyPackageImportDTO) -> ImportStudyPackageResultDTO:
        destination = request.destination
        if not destination.existing_block_id:
            raise ValueError("Bloco existente obrigatorio para atualizar.")
        subject, module, block = self.storage.get_block_by_id(destination.existing_block_id)
        if destination.description is not None:
            block.description = destination.description
        block = self._fill_block(block, request)
        self.storage.save_block(subject, module, block)
        self._sync_progress(block.id)
        _, _, block = self.storage.get_block_by_id(block.id)
        return ImportStudyPackageResultDTO(
            block=block,
            subject_name=subject.name,
            module_name=module.name,
            mode="update",
        )

    def _fill_block(self, block, request: StudyPackageImportDTO):
        package = request.package
        block.imported_files = [item.imported_file for item in request.extraction.files]
        block.extracted_content = request.extraction.combined_content
        block.generated_prompt = request.generated_prompt
        block.ai_response_raw = request.raw_ai_response
        block.ai_response = AIResponse(
            raw_text=request.raw_ai_response,
            parsed_successfully=not package.parser_warnings,
            parser_warnings=list(package.parser_warnings),
        )
        block.summary = Summary(package.summary_text) if package.summary_text.strip() else None
        block.summary_visual = package.summary_visual
        block.preferred_summary_mode = "visual" if package.summary_visual.strip() else "text"
        block.flashcards = [
            Flashcard(question=item.front, answer=item.back, source=item.source)
            for item in package.flashcards
        ]
        block.questions = [
            Question(
                statement=item.statement,
                alternatives=dict(item.alternatives),
                correct_answer=item.correct_answer,
                explanation=item.explanation,
            )
            for item in package.questions
        ]
        block.touch()
        return block

    def _sync_progress(self, block_id: str) -> None:
        progress_service = ProgressService(self.storage)
        progress_service.save_block_progress(block_id, progress_service.get_block_progress(block_id))
