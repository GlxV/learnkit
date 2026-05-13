from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.models.ai_response import AIResponse
from app.core.models.base import new_id, require_dict, utc_now
from app.core.models.extracted_content import ExtractedContent
from app.core.models.flashcard import Flashcard
from app.core.models.imported_file import ImportedFile
from app.core.models.question import Question
from app.core.models.summary import Summary


@dataclass(slots=True)
class StudyBlock:
    subject_id: str
    module_id: str
    title: str
    slug: str
    description: str | None = None
    imported_files: list[ImportedFile] = field(default_factory=list)
    extracted_content: ExtractedContent = field(default_factory=ExtractedContent)
    generated_prompt: str = ""
    ai_response_raw: str = ""
    ai_response: AIResponse | None = None
    summary_visual: str = ""
    preferred_summary_mode: str = "text"
    summary: Summary | None = None
    flashcards: list[Flashcard] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    id: str = field(default_factory=new_id)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "subject_id": self.subject_id,
            "module_id": self.module_id,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "imported_files": [item.to_dict() for item in self.imported_files],
            "extracted_content": self.extracted_content.to_dict(),
            "generated_prompt": self.generated_prompt,
            "ai_response_raw": self.ai_response_raw,
            "ai_response": self.ai_response.to_dict() if self.ai_response else None,
            "summary_visual": self.summary_visual,
            "preferred_summary_mode": self.preferred_summary_mode,
            "summary": self.summary.to_dict() if self.summary else None,
            "flashcards": [card.to_dict() for card in self.flashcards],
            "questions": [question.to_dict() for question in self.questions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StudyBlock":
        safe = require_dict(data)
        return cls(
            id=str(safe.get("id", new_id())),
            subject_id=str(safe.get("subject_id", "")),
            module_id=str(safe.get("module_id", "")),
            title=str(safe.get("title", "")),
            slug=str(safe.get("slug", "")),
            description=safe.get("description"),
            created_at=str(safe.get("created_at", utc_now())),
            updated_at=str(safe.get("updated_at", utc_now())),
            imported_files=[
                ImportedFile.from_dict(item) for item in safe.get("imported_files", [])
            ],
            extracted_content=ExtractedContent.from_dict(safe.get("extracted_content")),
            generated_prompt=str(safe.get("generated_prompt", "")),
            ai_response_raw=str(safe.get("ai_response_raw", "")),
            ai_response=AIResponse.from_dict(safe.get("ai_response")),
            summary_visual=str(safe.get("summary_visual", "")),
            preferred_summary_mode=str(safe.get("preferred_summary_mode", "text")),
            summary=Summary.from_dict(safe.get("summary")),
            flashcards=[Flashcard.from_dict(item) for item in safe.get("flashcards", [])],
            questions=[Question.from_dict(item) for item in safe.get("questions", [])],
        )
