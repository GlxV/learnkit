from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.core.models.ai_response import AIResponse
from app.core.models.flashcard import Flashcard
from app.core.models.question import Question
from app.core.models.summary import Summary


@dataclass(slots=True)
class ParsedAIResponse:
    ai_response: AIResponse
    summary: Summary
    summary_visual: str
    flashcards: list[Flashcard]
    questions: list[Question]
    warnings: list[str]


class AIResponseParser:
    REQUIRED_SECTIONS = ("FLASHCARDS", "PERGUNTAS")

    def parse(self, raw_text: str) -> ParsedAIResponse:
        warnings: list[str] = []
        sections = self._split_sections(raw_text)

        if "RESUMO" not in sections and "RESUMO_TEXTO" not in sections:
            warnings.append("Nenhuma secao RESUMO encontrada.")
        for section_name in self.REQUIRED_SECTIONS:
            if section_name not in sections:
                warnings.append(f"Nenhuma secao {section_name} encontrada.")

        summary = Summary(content=(sections.get("RESUMO_TEXTO") or sections.get("RESUMO", "")).strip())
        summary_visual = self._parse_visual_summary(sections.get("RESUMO_VISUAL", ""), warnings)
        flashcards = self._parse_flashcards(sections.get("FLASHCARDS", ""), warnings)
        questions = self._parse_questions(sections.get("PERGUNTAS", ""), warnings)
        ai_response = AIResponse(
            raw_text=raw_text,
            parsed_successfully=len(warnings) == 0,
            parser_warnings=warnings,
        )
        return ParsedAIResponse(ai_response, summary, summary_visual, flashcards, questions, warnings)

    def _split_sections(self, raw_text: str) -> dict[str, str]:
        matches = list(
            re.finditer(r"(?im)^#\s*(RESUMO(?:_TEXTO|_VISUAL)?|FLASHCARDS|PERGUNTAS)\s*$", raw_text)
        )
        sections: dict[str, str] = {}
        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(raw_text)
            sections[match.group(1).upper()] = raw_text[start:end].strip()
        return sections

    def _parse_visual_summary(self, section: str, warnings: list[str]) -> str:
        raw = section.strip()
        if not raw:
            return ""
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE).strip()
            raw = re.sub(r"\s*```$", "", raw).strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            warnings.append("RESUMO_VISUAL possui JSON invalido.")
            return ""
        if not isinstance(parsed, dict):
            warnings.append("RESUMO_VISUAL precisa ser um objeto JSON.")
            return ""
        return json.dumps(parsed, ensure_ascii=False, indent=2)

    def _parse_flashcards(self, section: str, warnings: list[str]) -> list[Flashcard]:
        if not section.strip():
            return []
        chunks = self._split_numbered_chunks(section, ("Card", "Flashcard")) or [section]
        flashcards: list[Flashcard] = []
        for index, chunk in enumerate(chunks, start=1):
            question = self._field(chunk, ("Pergunta", "Frente"))
            answer = self._field(chunk, ("Resposta", "Verso"))
            if not question:
                warnings.append(f"Card {index} sem pergunta.")
            if not answer:
                warnings.append(f"Card {index} sem resposta.")
            if question or answer:
                flashcards.append(Flashcard(question=question, answer=answer))
        return flashcards

    def _parse_questions(self, section: str, warnings: list[str]) -> list[Question]:
        if not section.strip():
            return []
        chunks = self._split_numbered_chunks(section, ("Pergunta", "Questao", "Questão")) or [section]
        questions: list[Question] = []
        for index, chunk in enumerate(chunks, start=1):
            statement = self._field(chunk, ("Enunciado", "Pergunta"))
            alternatives = self._alternatives(chunk)
            correct_answer = self._normalize_answer(
                self._field(chunk, ("Gabarito", "Resposta correta", "Alternativa correta"))
            )
            explanation = self._field(chunk, ("Explicacao", "Explicação", "Justificativa"))

            if not statement:
                warnings.append(f"Pergunta {index} sem enunciado.")
            if len(alternatives) < 4:
                warnings.append(f"Pergunta {index} tem menos de 4 alternativas.")
            if not correct_answer:
                warnings.append(f"Pergunta {index} sem gabarito.")
            if statement or alternatives or correct_answer:
                questions.append(
                    Question(
                        statement=statement,
                        alternatives=alternatives,
                        correct_answer=correct_answer,
                        explanation=explanation or None,
                    )
                )
        return questions

    def _split_numbered_chunks(self, section: str, names: tuple[str, ...]) -> list[str]:
        names_pattern = "|".join(re.escape(name) for name in names)
        pattern = rf"(?im)^##\s*(?:{names_pattern})\s+\d+\s*$"
        matches = list(re.finditer(pattern, section))
        chunks: list[str] = []
        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
            chunks.append(section[start:end].strip())
        return chunks

    def _field(self, chunk: str, labels: tuple[str, ...]) -> str:
        labels_pattern = "|".join(re.escape(label) for label in labels)
        stop_labels = (
            r"Pergunta|Frente|Resposta|Verso|Enunciado|Gabarito|"
            r"Resposta correta|Alternativa correta|Explicacao|Explicação|Justificativa"
        )
        pattern = (
            rf"(?ims)^\s*(?:[-*]\s*)?(?:{labels_pattern})\s*[:\-]\s*"
            rf"(.+?)(?=^\s*(?:[-*]\s*)?(?:{stop_labels})\s*[:\-]|^\s*[A-D]\s*[\)\.\-:]|^##\s+|\Z)"
        )
        match = re.search(pattern, chunk)
        return self._clean(match.group(1)) if match else ""

    def _alternatives(self, chunk: str) -> dict[str, str]:
        alternatives: dict[str, str] = {}
        matches = list(re.finditer(r"(?im)^\s*(?:[-*]\s*)?\**([A-D])\**\s*[\)\.\-:]\s*(.+?)\s*$", chunk))
        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(chunk)
            first_line = match.group(2).strip()
            continuation = chunk[start:end].strip()
            continuation = re.split(
                r"(?im)^\s*(?:Gabarito|Resposta correta|Alternativa correta|Explicacao|Explicação|Justificativa)\s*[:\-]",
                continuation,
                maxsplit=1,
            )[0].strip()
            value = self._clean("\n".join(part for part in [first_line, continuation] if part))
            alternatives[match.group(1).upper()] = value
        return alternatives

    def _normalize_answer(self, value: str) -> str:
        match = re.search(r"[A-D]", value.upper())
        return match.group(0) if match else ""

    def _clean(self, value: str) -> str:
        lines = [line.strip() for line in value.strip().splitlines()]
        return "\n".join(line for line in lines if line).strip()
