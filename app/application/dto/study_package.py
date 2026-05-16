from __future__ import annotations

from dataclasses import dataclass, field

from app.core.extractors.file_extractor import FileExtractionResult
from app.core.models.study_block import StudyBlock


STUDY_PACKAGE_SCHEMA_VERSION = "learnkit.study_package.v1"


@dataclass(slots=True)
class FlashcardDTO:
    front: str
    back: str
    source: str | None = None


@dataclass(slots=True)
class QuestionDTO:
    statement: str
    alternatives: dict[str, str]
    correct_answer: str
    explanation: str | None = None


@dataclass(slots=True)
class StudyPackageDTO:
    schema_version: str = STUDY_PACKAGE_SCHEMA_VERSION
    summary_text: str = ""
    summary_visual: str = ""
    flashcards: list[FlashcardDTO] = field(default_factory=list)
    questions: list[QuestionDTO] = field(default_factory=list)
    parser_warnings: list[str] = field(default_factory=list)

    def has_content(self) -> bool:
        return bool(
            self.summary_text.strip()
            or self.summary_visual.strip()
            or self.flashcards
            or self.questions
        )


@dataclass(slots=True)
class ImportDestinationDTO:
    subject_name: str
    module_name: str
    block_title: str = ""
    existing_block_id: str | None = None
    description: str | None = None


@dataclass(slots=True)
class StudyPackageImportDTO:
    extraction: FileExtractionResult
    generated_prompt: str
    raw_ai_response: str
    package: StudyPackageDTO
    destination: ImportDestinationDTO
    mode: str = "create"


@dataclass(slots=True)
class ImportStudyPackageResultDTO:
    block: StudyBlock
    subject_name: str
    module_name: str
    created_subject: bool = False
    created_module: bool = False
    mode: str = "create"
