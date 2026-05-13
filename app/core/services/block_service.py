from __future__ import annotations

import json
from pathlib import Path

from app.core.extractors.file_extractor import FileExtractionResult, FileExtractor
from app.core.importer.ai_response_parser import AIResponseParser, ParsedAIResponse
from app.core.models.extracted_content import ExtractedContent
from app.core.models.flashcard import Flashcard
from app.core.models.question import Question
from app.core.models.study_block import StudyBlock
from app.core.models.summary import Summary
from app.core.prompt.prompt_builder import PromptBuilder, PromptOptions
from app.core.storage.local_storage import LocalStorage


class BlockService:
    def __init__(
        self,
        storage: LocalStorage,
        file_extractor: FileExtractor | None = None,
        prompt_builder: PromptBuilder | None = None,
        ai_response_parser: AIResponseParser | None = None,
    ) -> None:
        self.storage = storage
        self.file_extractor = file_extractor or FileExtractor()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.ai_response_parser = ai_response_parser or AIResponseParser()

    def create_block(
        self,
        subject_ref: str,
        module_ref: str,
        title: str,
        file_paths: list[str | Path] | None = None,
        description: str | None = None,
    ) -> StudyBlock:
        self._validate_title(title)
        block = self.storage.create_block(subject_ref, module_ref, title.strip(), description)
        if file_paths:
            block = self.import_files_to_block(block.id, file_paths)
        self._ensure_progress_file(block.id)
        return block

    def list_blocks(self, subject_ref: str, module_ref: str) -> list[StudyBlock]:
        return self.storage.list_blocks(subject_ref, module_ref)

    def rename_block(
        self,
        subject_ref: str,
        module_ref: str,
        block_ref: str,
        new_title: str,
    ) -> StudyBlock:
        self._validate_title(new_title)
        subject, module, block = self.storage.get_block(subject_ref, module_ref, block_ref)
        block.title = new_title.strip()
        block.touch()
        self.storage.save_block(subject, module, block)
        self._ensure_progress_file(block.id)
        return block

    def delete_block(self, subject_ref: str, module_ref: str, block_ref: str) -> None:
        self.storage.delete_block(subject_ref, module_ref, block_ref)

    def import_files_to_block(
        self,
        block_id: str,
        file_paths: list[str | Path],
    ) -> StudyBlock:
        subject, module, block = self.storage.get_block_by_id(block_id)
        extraction = self.file_extractor.extract_files(file_paths)
        block.imported_files.extend([item.imported_file for item in extraction.files])
        block.extracted_content = self._merge_extracted_content(
            block.extracted_content,
            extraction.combined_content,
        )
        block.touch()
        self.storage.save_block(subject, module, block)
        return block

    def export_text(
        self,
        subject_ref: str,
        module_ref: str,
        block_ref: str,
        output_path: str | Path | None = None,
        file_format: str = "md",
    ) -> Path:
        subject, module, block = self.storage.get_block(subject_ref, module_ref, block_ref)
        extension = file_format.lower().lstrip(".")
        if output_path is None:
            output_path = (
                self.storage.block_path(subject.slug, module.slug, block.slug)
                / f"extracted_text.{extension}"
            )
        return self.file_extractor.export_block_text(
            block.extracted_content.source_files,
            block.extracted_content.text,
            output_path,
            extension,
        )

    def generate_prompt(
        self,
        subject_ref: str,
        module_ref: str,
        block_ref: str,
        options: PromptOptions | None = None,
    ) -> str:
        subject, module, block = self.storage.get_block(subject_ref, module_ref, block_ref)
        prompt = self.prompt_builder.build(
            subject_name=subject.name,
            module_name=module.name,
            block_title=block.title,
            extracted_content=block.extracted_content,
            options=options,
        )
        block.generated_prompt = prompt
        block.touch()
        self.storage.save_block(subject, module, block)
        return prompt

    def import_ai_response(
        self,
        subject_ref: str,
        module_ref: str,
        block_ref: str,
        response_text: str,
    ) -> StudyBlock:
        subject, module, block = self.storage.get_block(subject_ref, module_ref, block_ref)
        parsed = self.ai_response_parser.parse(response_text)
        block.ai_response_raw = response_text
        block.ai_response = parsed.ai_response
        block.summary = parsed.summary
        block.summary_visual = parsed.summary_visual
        block.preferred_summary_mode = "visual" if parsed.summary_visual else "text"
        block.flashcards = parsed.flashcards
        block.questions = parsed.questions
        block.touch()
        self.storage.save_block(subject, module, block)
        self._ensure_progress_file(block.id)
        return block

    def import_ai_response_file(
        self,
        subject_ref: str,
        module_ref: str,
        block_ref: str,
        response_path: str | Path,
    ) -> StudyBlock:
        text = Path(response_path).read_text(encoding="utf-8")
        return self.import_ai_response(subject_ref, module_ref, block_ref, text)

    def save_imported_package(
        self,
        subject_ref: str,
        module_ref: str,
        title: str,
        extraction: FileExtractionResult,
        generated_prompt: str,
        response_text: str,
        parsed_response: ParsedAIResponse,
        description: str | None = None,
    ) -> StudyBlock:
        self._validate_title(title)
        block = self.storage.create_block(subject_ref, module_ref, title.strip(), description)
        subject, module, block = self.storage.get_block_by_id(block.id)
        block.imported_files = [item.imported_file for item in extraction.files]
        block.extracted_content = extraction.combined_content
        block.generated_prompt = generated_prompt
        block.ai_response_raw = response_text
        block.ai_response = parsed_response.ai_response
        block.summary = (
            parsed_response.summary if parsed_response.summary.content.strip() else None
        )
        block.summary_visual = parsed_response.summary_visual
        block.preferred_summary_mode = "visual" if parsed_response.summary_visual else "text"
        block.flashcards = parsed_response.flashcards
        block.questions = parsed_response.questions
        block.touch()
        self.storage.save_block(subject, module, block)
        self._ensure_progress_file(block.id)
        return block

    def show_summary(self, subject_ref: str, module_ref: str, block_ref: str) -> Summary | None:
        return self.storage.get_block(subject_ref, module_ref, block_ref)[2].summary

    def list_flashcards(
        self,
        subject_ref: str,
        module_ref: str,
        block_ref: str,
    ) -> list[Flashcard]:
        return self.storage.get_block(subject_ref, module_ref, block_ref)[2].flashcards

    def list_questions(
        self,
        subject_ref: str,
        module_ref: str,
        block_ref: str,
    ) -> list[Question]:
        return self.storage.get_block(subject_ref, module_ref, block_ref)[2].questions

    def update_study_materials(
        self,
        block_id: str,
        summary_markdown: str,
        flashcards_data: list[dict[str, str]],
        questions_data: list[dict[str, object]],
    ) -> StudyBlock:
        subject, module, block = self.storage.get_block_by_id(block_id)
        block.summary = Summary(content=summary_markdown)
        block.flashcards = [
            Flashcard(
                question=str(item.get("question", "")),
                answer=str(item.get("answer", "")),
                source=item.get("source"),
            )
            for item in flashcards_data
        ]
        block.questions = [
            Question(
                statement=str(item.get("statement", "")),
                alternatives={
                    str(key): str(value)
                    for key, value in dict(item.get("alternatives", {})).items()
                },
                correct_answer=str(item.get("correct_answer", "")),
                explanation=(
                    str(item["explanation"]) if item.get("explanation") is not None else None
                ),
            )
            for item in questions_data
        ]
        block.touch()
        self.storage.save_block(subject, module, block)
        self._ensure_progress_file(block.id)
        return block

    def update_summary_modes(
        self,
        block_id: str,
        summary_markdown: str | None = None,
        summary_visual: str | None = None,
        preferred_summary_mode: str | None = None,
    ) -> StudyBlock:
        subject, module, block = self.storage.get_block_by_id(block_id)
        if summary_markdown is not None:
            block.summary = Summary(content=summary_markdown) if summary_markdown.strip() else None

        if summary_visual is not None:
            block.summary_visual = self._normalize_summary_visual(summary_visual)

        if preferred_summary_mode is not None:
            if preferred_summary_mode not in {"text", "visual"}:
                raise ValueError("Modo de resumo invalido.")
            if preferred_summary_mode == "visual" and not block.summary_visual.strip():
                raise ValueError("Resumo visual precisa existir para usar o modo visual.")
            block.preferred_summary_mode = preferred_summary_mode
        elif block.preferred_summary_mode == "visual" and not block.summary_visual.strip():
            block.preferred_summary_mode = "text"

        block.touch()
        self.storage.save_block(subject, module, block)
        return block

    def _merge_extracted_content(
        self,
        current: ExtractedContent,
        new_content: ExtractedContent,
    ) -> ExtractedContent:
        pieces = [part for part in [current.text.strip(), new_content.text.strip()] if part]
        source_files = current.source_files + [
            item for item in new_content.source_files if item not in current.source_files
        ]
        return ExtractedContent(
            text="\n\n".join(pieces),
            source_files=source_files,
        )

    def _validate_title(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("O titulo do bloco nao pode ficar vazio.")

    def _normalize_summary_visual(self, value: str) -> str:
        raw = value.strip()
        if not raw:
            return ""
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Resumo visual possui JSON invalido: {exc.msg}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("Resumo visual precisa ser um objeto JSON.")
        return json.dumps(parsed, ensure_ascii=False, indent=2)

    def _ensure_progress_file(self, block_id: str) -> None:
        from app.core.services.progress_service import ProgressService

        service = ProgressService(self.storage)
        service.save_block_progress(block_id, service.get_block_progress(block_id))
