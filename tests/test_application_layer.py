from __future__ import annotations

from pathlib import Path

from app.application.dto.study_package import (
    ImportDestinationDTO,
    StudyPackageDTO,
    StudyPackageImportDTO,
)
from app.application.query_services.dashboard_query_service import DashboardQueryService
from app.application.query_services.search_query_service import SearchQueryService
from app.application.use_cases.generate_prompt import GeneratePromptUseCase
from app.application.use_cases.import_study_package import ImportStudyPackageUseCase
from app.application.use_cases.parse_ai_response import ParseAIResponseUseCase
from app.core.database import SQLiteStorage
from app.core.extractors.file_extractor import ExtractedFileResult, FileExtractionResult
from app.core.importer.ai_response_parser import AIResponseParser
from app.core.models.extracted_content import ExtractedContent
from app.core.models.imported_file import ImportedFile
from app.core.prompt.prompt_builder import PromptOptions
from app.core.services.progress_service import ProgressService
from app.infrastructure.sqlite.migrations import Migration, MigrationRunner


def _extraction(file_name: str = "aula.md", text: str = "conteudo extraido") -> FileExtractionResult:
    imported_file = ImportedFile(
        original_path=str(Path("materiais") / file_name),
        file_name=file_name,
        file_type=file_name.rsplit(".", 1)[-1],
        file_size=len(text.encode("utf-8")),
        extraction_status="success",
    )
    return FileExtractionResult(
        files=[
            ExtractedFileResult(
                imported_file=imported_file,
                text=text,
                character_count=len(text),
                word_count=len(text.split()),
            )
        ],
        combined_content=ExtractedContent(text=text, source_files=[file_name]),
        file_texts={file_name: text},
    )


def _raw_response(title: str = "Resumo", card: str = "O que e teste?", question: str = "Qual opcao?") -> str:
    return f"""# RESUMO_TEXTO

{title}

# RESUMO_VISUAL
{{"title": "{title}", "sections": []}}

# FLASHCARDS

## Card 1
Pergunta: {card}
Resposta: Resposta.

# PERGUNTAS

## Pergunta 1
Enunciado: {question}
A) A certa
B) B errada
C) C errada
D) D errada
Gabarito: A
Explicacao: Porque A esta correta.
"""


def _package(raw_response: str | None = None) -> StudyPackageDTO:
    return ParseAIResponseUseCase().execute(raw_response or _raw_response())


def test_generate_prompt_use_case_wraps_existing_prompt_builder() -> None:
    prompt = GeneratePromptUseCase().execute(
        subject_name="Banco de Dados",
        module_name="Prova 1",
        block_title="Modelo Relacional",
        extracted_content=ExtractedContent(text="texto sobre chaves"),
        options=PromptOptions(flashcard_count=4, question_count=2),
    )

    assert '"schema_version": "learnkit.study_package.v1"' in prompt
    assert '"summary_text"' in prompt
    assert "4 flashcards" in prompt
    assert "2 perguntas" in prompt
    assert "texto sobre chaves" in prompt


def test_parse_ai_response_use_case_returns_versioned_dto_with_markdown_compatibility() -> None:
    dto = ParseAIResponseUseCase().execute(_raw_response())

    assert dto.schema_version == "learnkit.study_package.v1"
    assert dto.summary_text == "Resumo"
    assert '"title": "Resumo"' in dto.summary_visual
    assert dto.flashcards[0].front == "O que e teste?"
    assert dto.questions[0].correct_answer == "A"
    assert dto.parser_warnings == []


def test_parse_ai_response_use_case_accepts_versioned_json_package() -> None:
    dto = ParseAIResponseUseCase().execute(
        """
        {
          "schema_version": "learnkit.study_package.v1",
          "summary_text": "Resumo JSON",
          "summary_visual": {"title": "Visual"},
          "flashcards": [{"front": "Frente?", "back": "Verso"}],
          "questions": [
            {
              "statement": "Pergunta?",
              "alternatives": {"A": "Um", "B": "Dois", "C": "Tres", "D": "Quatro"},
              "correct_answer": "A",
              "explanation": "Porque sim."
            }
          ]
        }
        """
    )

    assert dto.summary_text == "Resumo JSON"
    assert '"title": "Visual"' in dto.summary_visual
    assert dto.flashcards[0].front == "Frente?"
    assert dto.questions[0].alternatives["D"] == "Quatro"


def test_parse_ai_response_use_case_accepts_fenced_json_package() -> None:
    dto = ParseAIResponseUseCase().execute(
        """```json
        {
          "schema_version": "learnkit.study_package.v1",
          "summary_text": "Resumo cercado",
          "summary_visual": {},
          "flashcards": [{"front": "F?", "back": "B"}],
          "questions": []
        }
        ```"""
    )

    assert dto.summary_text == "Resumo cercado"
    assert dto.flashcards[0].front == "F?"


def test_import_study_package_use_case_create_persists_materials_and_progress(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    use_case = ImportStudyPackageUseCase(storage)

    result = use_case.execute(
        StudyPackageImportDTO(
            extraction=_extraction(text="texto inicial"),
            generated_prompt="prompt gerado",
            raw_ai_response=_raw_response("Resumo inicial"),
            package=_package(_raw_response("Resumo inicial")),
            destination=ImportDestinationDTO(
                subject_name="Estrutura de Dados",
                module_name="Pilhas",
                block_title="Introducao",
            ),
            mode="create",
        )
    )

    _, _, block = storage.get_block_by_id(result.block.id)
    progress = ProgressService(storage).get_block_progress(block.id)

    assert result.created_subject is True
    assert result.created_module is True
    assert block.summary is not None
    assert block.summary.content == "Resumo inicial"
    assert '"title": "Resumo inicial"' in block.summary_visual
    assert block.flashcards[0].question == "O que e teste?"
    assert block.questions[0].statement == "Qual opcao?"
    assert progress.flashcards_total == 1
    assert progress.questions_total == 1


def test_import_study_package_use_case_update_replaces_materials_and_prunes_progress(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    use_case = ImportStudyPackageUseCase(storage)
    created = use_case.execute(
        StudyPackageImportDTO(
            extraction=_extraction(text="texto antigo"),
            generated_prompt="prompt antigo",
            raw_ai_response=_raw_response("Resumo antigo", "Card antigo?", "Pergunta antiga?"),
            package=_package(_raw_response("Resumo antigo", "Card antigo?", "Pergunta antiga?")),
            destination=ImportDestinationDTO(
                subject_name="Estrutura de Dados",
                module_name="Pilhas",
                block_title="Introducao",
            ),
            mode="create",
        )
    )
    old_card_id = created.block.flashcards[0].id
    old_question_id = created.block.questions[0].id
    progress_service = ProgressService(storage)
    progress_service.record_flashcard(created.block.id, old_card_id, "easy")
    progress_service.record_question(created.block.id, old_question_id, "A", "A")

    updated = use_case.execute(
        StudyPackageImportDTO(
            extraction=_extraction(file_name="novo.md", text="texto novo"),
            generated_prompt="prompt novo",
            raw_ai_response=_raw_response("Resumo novo", "Card novo?", "Pergunta nova?"),
            package=_package(_raw_response("Resumo novo", "Card novo?", "Pergunta nova?")),
            destination=ImportDestinationDTO(
                subject_name="Estrutura de Dados",
                module_name="Pilhas",
                existing_block_id=created.block.id,
            ),
            mode="update",
        )
    )
    progress = progress_service.get_block_progress(created.block.id)

    assert updated.block.id == created.block.id
    assert updated.block.generated_prompt == "prompt novo"
    assert updated.block.flashcards[0].question == "Card novo?"
    assert old_card_id not in progress.reviewed_flashcards
    assert old_question_id not in progress.answered_questions
    assert progress.flashcards_reviewed == 0
    assert progress.questions_answered == 0


def test_search_query_service_finds_nested_content(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    ImportStudyPackageUseCase(storage).execute(
        StudyPackageImportDTO(
            extraction=_extraction(text="texto"),
            generated_prompt="prompt",
            raw_ai_response=_raw_response("Resumo sobre arvores", "O que e arvore binaria?", "Qual estrutura usa nos?"),
            package=_package(_raw_response("Resumo sobre arvores", "O que e arvore binaria?", "Qual estrutura usa nos?")),
            destination=ImportDestinationDTO(
                subject_name="Computacao",
                module_name="Grafos",
                block_title="Arvores",
            ),
            mode="create",
        )
    )

    results = SearchQueryService(storage).search("binaria")

    assert results
    assert results[0][2]["kind"] == "flashcard"


def test_dashboard_query_service_delegates_dashboard_and_global_stats(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    result = ImportStudyPackageUseCase(storage).execute(
        StudyPackageImportDTO(
            extraction=_extraction(text="texto"),
            generated_prompt="prompt",
            raw_ai_response=_raw_response(),
            package=_package(),
            destination=ImportDestinationDTO("Fisica", "Cinematica", "Velocidade"),
            mode="create",
        )
    )
    ProgressService(storage).record_flashcard(result.block.id, result.block.flashcards[0].id, "again")

    service = DashboardQueryService(storage)
    dashboard = service.review_dashboard()
    stats = service.global_stats()

    assert dashboard["summary"]["due_flashcards"] == 1
    assert stats.total_subjects == 1
    assert stats.total_flashcards == 1


def test_migration_runner_applies_migrations_once(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    runner = MigrationRunner(
        storage.connect,
        [
            Migration(
                version=999,
                name="test_once",
                statements=("CREATE TABLE IF NOT EXISTS migration_probe (id INTEGER PRIMARY KEY);",),
            )
        ],
    )

    first = runner.apply_pending()
    second = runner.apply_pending()
    applied = runner.applied_versions()

    assert first == [999]
    assert second == []
    assert 999 in applied
