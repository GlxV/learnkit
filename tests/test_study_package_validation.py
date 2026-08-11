from __future__ import annotations

from app.application.dto.study_package import FlashcardDTO, QuestionDTO, StudyPackageDTO
from app.application.use_cases.validate_study_package import ValidateStudyPackageUseCase


def test_validation_reports_counts_severity_and_filters_invalid_items() -> None:
    package = StudyPackageDTO(
        summary_text="Resumo curto.",
        summary_visual='{"title":"Visual","sections":[]}',
        flashcards=[
            FlashcardDTO("Frente", "Verso"),
            FlashcardDTO("Sem resposta", ""),
        ],
        questions=[
            QuestionDTO(
                "Questão válida?",
                {"A": "A", "B": "B", "C": "C", "D": "D"},
                "A",
            ),
            QuestionDTO("Questão incompleta?", {"A": "A"}, "A"),
        ],
        parser_warnings=["Seção opcional ausente."],
    )

    report = ValidateStudyPackageUseCase().execute(package)

    assert report.can_save is True
    assert report.fatal_issues == []
    assert report.flashcards_total == 2
    assert report.flashcards_valid == 1
    assert report.questions_total == 2
    assert report.questions_valid == 1
    assert len(report.warning_issues) == 3
    assert len(report.usable_package.flashcards) == 1
    assert len(report.usable_package.questions) == 1


def test_validation_blocks_package_without_any_usable_content() -> None:
    report = ValidateStudyPackageUseCase().execute(
        StudyPackageDTO(
            flashcards=[FlashcardDTO("", "")],
            questions=[QuestionDTO("", {"A": "A"}, "Z")],
        )
    )

    assert report.can_save is False
    assert report.fatal_issues
