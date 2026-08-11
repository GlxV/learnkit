from __future__ import annotations

import json

from app.application.dto.study_package import (
    FlashcardDTO,
    QuestionDTO,
    StudyPackageDTO,
)
from app.application.dto.visual_summary import dump_visual_summary
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
            summary_visual=dump_visual_summary(parsed.summary_visual),
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
        parser_warnings = self._warning_list(data.get("parser_warnings", []))
        flashcard_items = self._object_list(
            data.get("flashcards", []), "flashcards", parser_warnings
        )
        question_items = self._object_list(
            data.get("questions", []), "questions", parser_warnings
        )
        flashcards = [
            FlashcardDTO(
                front=str(item.get("front", "")),
                back=str(item.get("back", "")),
                source=(str(item["source"]) if item.get("source") is not None else None),
            )
            for item in flashcard_items
        ]
        questions: list[QuestionDTO] = []
        for index, item in enumerate(question_items, start=1):
            raw_alternatives = item.get("alternatives", {})
            if not isinstance(raw_alternatives, dict):
                parser_warnings.append(
                    f"Pergunta {index} possui alternatives em formato inválido."
                )
                raw_alternatives = {}
            questions.append(
                QuestionDTO(
                    statement=str(item.get("statement", "")),
                    alternatives={
                        str(key): str(value) for key, value in raw_alternatives.items()
                    },
                    correct_answer=str(item.get("correct_answer", "")),
                    explanation=(
                        str(item["explanation"])
                        if item.get("explanation") is not None
                        else None
                    ),
                )
            )
        summary_visual = data.get("summary_visual", "")
        return StudyPackageDTO(
            schema_version=schema_version,
            summary_text=str(data.get("summary_text", "")),
            summary_visual=dump_visual_summary(summary_visual),
            flashcards=flashcards,
            questions=questions,
            parser_warnings=parser_warnings,
        )

    def _object_list(
        self,
        value: object,
        field_name: str,
        warnings: list[str],
    ) -> list[dict[str, object]]:
        if not isinstance(value, list):
            warnings.append(f"Campo {field_name} precisa ser uma lista.")
            return []
        items: list[dict[str, object]] = []
        for index, item in enumerate(value, start=1):
            if isinstance(item, dict):
                items.append(item)
            else:
                warnings.append(f"Item {index} de {field_name} foi ignorado por formato inválido.")
        return items

    def _warning_list(self, value: object) -> list[str]:
        if not isinstance(value, list):
            return ["Campo parser_warnings precisa ser uma lista."]
        return [str(warning).strip() for warning in value if str(warning).strip()]

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
