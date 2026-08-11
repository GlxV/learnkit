from __future__ import annotations

from app.application.dto.study_package import FlashcardDTO, QuestionDTO, StudyPackageDTO
from app.application.dto.study_package import ImportDestinationDTO, StudyPackageImportDTO
from app.application.use_cases.import_study_package import ImportStudyPackageUseCase
from app.application.use_cases.parse_ai_response import ParseAIResponseUseCase
from app.application.use_cases.validate_study_package import ValidateStudyPackageUseCase
from app.core.database import SQLiteStorage
from app.core.extractors.file_extractor import FileExtractionResult
from app.core.models.extracted_content import ExtractedContent


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


def test_json_parser_turns_malformed_collection_shapes_into_warnings() -> None:
    package = ParseAIResponseUseCase().execute(
        '{"summary_text":"Resumo preservado",'
        '"flashcards":null,"questions":null,"parser_warnings":null}'
    )

    report = ValidateStudyPackageUseCase().execute(package)

    assert report.can_save is True
    assert report.summary_found is True
    assert report.flashcards_total == 0
    assert report.questions_total == 0
    assert len(report.warning_issues) == 3


def test_validation_normalizes_question_contract_before_import() -> None:
    package = ParseAIResponseUseCase().execute(
        '{"questions":[{"statement":"Questão?",'
        '"alternatives":{" a ":"Um","b":"Dois","C":"Três","d":"Quatro"},'
        '"correct_answer":" a "}]}'
    )

    report = ValidateStudyPackageUseCase().execute(package)

    assert report.can_save is True
    assert report.questions_valid == 1
    question = report.usable_package.questions[0]
    assert question.alternatives == {
        "A": "Um",
        "B": "Dois",
        "C": "Três",
        "D": "Quatro",
    }
    assert question.correct_answer == "A"


def test_normalized_question_persists_with_usable_alternatives(tmp_path) -> None:
    raw = (
        '{"questions":[{"statement":"Questão?",'
        '"alternatives":{"a":"Um","b":"Dois","c":"Três","d":"Quatro"},'
        '"correct_answer":"a"}]}'
    )
    parsed = ParseAIResponseUseCase().execute(raw)
    package = ValidateStudyPackageUseCase().execute(parsed).usable_package
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)

    result = ImportStudyPackageUseCase(storage).execute(
        StudyPackageImportDTO(
            extraction=FileExtractionResult(
                combined_content=ExtractedContent(text="Fonte de estudo")
            ),
            generated_prompt="prompt",
            raw_ai_response=raw,
            package=package,
            destination=ImportDestinationDTO("Matéria", "Módulo", "Bloco"),
        )
    )

    loaded = storage.get_block_by_id(result.block.id)[2]
    assert loaded.questions[0].alternatives == {
        "A": "Um",
        "B": "Dois",
        "C": "Três",
        "D": "Quatro",
    }
    assert loaded.questions[0].correct_answer == "A"
