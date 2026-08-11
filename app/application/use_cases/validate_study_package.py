from __future__ import annotations

from dataclasses import replace

from app.application.dto.study_package import FlashcardDTO, QuestionDTO, StudyPackageDTO
from app.application.dto.study_package_validation import (
    StudyPackageValidationDTO,
    ValidationIssueDTO,
)
from app.application.dto.visual_summary import parse_visual_summary


class ValidateStudyPackageUseCase:
    """Classifies and canonicalizes parser output without parsing raw text again."""

    def execute(self, package: StudyPackageDTO) -> StudyPackageValidationDTO:
        issues: list[ValidationIssueDTO] = []
        summary_found = bool(package.summary_text.strip())
        visual_valid = False
        if package.summary_visual.strip():
            visual_valid = parse_visual_summary(package.summary_visual) is not None
            if visual_valid:
                issues.append(ValidationIssueDTO("info", "Resumo visual válido."))
            else:
                issues.append(ValidationIssueDTO("warning", "Resumo visual encontrado, mas inválido."))
        else:
            issues.append(ValidationIssueDTO("info", "Resumo visual não encontrado."))

        if summary_found:
            issues.append(ValidationIssueDTO("info", "Resumo textual encontrado."))
        else:
            issues.append(ValidationIssueDTO("info", "Resumo textual não encontrado."))

        normalized_flashcards = [_normalize_flashcard(card) for card in package.flashcards]
        normalized_questions = [_normalize_question(question) for question in package.questions]
        valid_flashcards = [card for card in normalized_flashcards if _valid_flashcard(card)]
        valid_questions = [question for question in normalized_questions if _valid_question(question)]
        invalid_flashcards = len(package.flashcards) - len(valid_flashcards)
        invalid_questions = len(package.questions) - len(valid_questions)
        if invalid_flashcards:
            issues.append(
                ValidationIssueDTO(
                    "warning",
                    f"{invalid_flashcards} flashcard(s) foram ignorados por falta de pergunta ou resposta.",
                )
            )
        if invalid_questions:
            issues.append(
                ValidationIssueDTO(
                    "warning",
                    f"{invalid_questions} pergunta(s) foram ignoradas por estrutura incompleta.",
                )
            )
        for warning in package.parser_warnings:
            if warning.strip():
                issues.append(ValidationIssueDTO("warning", warning.strip()))

        has_usable_content = bool(summary_found or visual_valid or valid_flashcards or valid_questions)
        if not has_usable_content:
            issues.insert(
                0,
                ValidationIssueDTO(
                    "fatal",
                    "Nenhum conteúdo utilizável foi encontrado no pacote.",
                ),
            )

        usable_package = replace(
            package,
            summary_visual=package.summary_visual if visual_valid else "",
            flashcards=valid_flashcards,
            questions=valid_questions,
        )
        return StudyPackageValidationDTO(
            package=package,
            usable_package=usable_package,
            summary_found=summary_found,
            visual_valid=visual_valid,
            flashcards_total=len(package.flashcards),
            flashcards_valid=len(valid_flashcards),
            questions_total=len(package.questions),
            questions_valid=len(valid_questions),
            issues=issues,
        )


def _normalize_flashcard(card: FlashcardDTO) -> FlashcardDTO:
    return FlashcardDTO(
        front=card.front.strip(),
        back=card.back.strip(),
        source=card.source,
    )


def _normalize_question(question: QuestionDTO) -> QuestionDTO:
    alternatives = {
        str(key).strip().upper(): str(value).strip()
        for key, value in question.alternatives.items()
        if str(key).strip()
    }
    return QuestionDTO(
        statement=question.statement.strip(),
        alternatives=alternatives,
        correct_answer=question.correct_answer.strip().upper(),
        explanation=question.explanation,
    )


def _valid_flashcard(card: FlashcardDTO) -> bool:
    return bool(card.front and card.back)


def _valid_question(question: QuestionDTO) -> bool:
    return bool(
        question.statement
        and all(question.alternatives.get(letter) for letter in ("A", "B", "C", "D"))
        and question.correct_answer in {"A", "B", "C", "D"}
    )

__all__ = [
    "StudyPackageValidationDTO",
    "ValidateStudyPackageUseCase",
    "ValidationIssueDTO",
]
