from __future__ import annotations

import json

from app.application.dto.study_package import (
    FlashcardDTO,
    QuestionDTO,
    StudyPackageDTO,
)
from app.core.importer.ai_response_parser import AIResponseParser


class ParseAIResponseUseCase:
    def __init__(self, parser: AIResponseParser | None = None) -> None:
        self.parser = parser or AIResponseParser()

    def execute(self, raw_text: str) -> StudyPackageDTO:
        json_package = self._parse_json_package(raw_text)
        if json_package is not None:
            return json_package
        parsed = self.parser.parse(raw_text)
        return StudyPackageDTO(
            summary_text=parsed.summary.content,
            summary_visual=parsed.summary_visual,
            flashcards=[
                FlashcardDTO(front=card.question, back=card.answer, source=card.source)
                for card in parsed.flashcards
            ],
            questions=[
                QuestionDTO(
                    statement=question.statement,
                    alternatives=dict(question.alternatives),
                    correct_answer=question.correct_answer,
                    explanation=question.explanation,
                )
                for question in parsed.questions
            ],
            parser_warnings=list(parsed.warnings),
        )

    def _parse_json_package(self, raw_text: str) -> StudyPackageDTO | None:
        raw = raw_text.strip()
        raw = self._strip_json_fence(raw)
        if not raw.startswith("{"):
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        schema_version = str(data.get("schema_version", "learnkit.study_package.v1"))
        flashcards = [
            FlashcardDTO(
                front=str(item.get("front", "")),
                back=str(item.get("back", "")),
                source=item.get("source"),
            )
            for item in data.get("flashcards", [])
            if isinstance(item, dict)
        ]
        questions = [
            QuestionDTO(
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
            for item in data.get("questions", [])
            if isinstance(item, dict)
        ]
        summary_visual = data.get("summary_visual", "")
        if isinstance(summary_visual, dict):
            summary_visual = json.dumps(summary_visual, ensure_ascii=False, indent=2)
        return StudyPackageDTO(
            schema_version=schema_version,
            summary_text=str(data.get("summary_text", "")),
            summary_visual=str(summary_visual or ""),
            flashcards=flashcards,
            questions=questions,
            parser_warnings=[
                str(warning)
                for warning in data.get("parser_warnings", [])
                if str(warning).strip()
            ],
        )

    def _strip_json_fence(self, raw: str) -> str:
        if not raw.startswith("```"):
            return raw
        lines = raw.splitlines()
        if not lines:
            return raw
        opener = lines[0].strip().lower()
        if opener not in {"```", "```json"}:
            return raw
        if lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip()
        return "\n".join(lines[1:]).strip()
