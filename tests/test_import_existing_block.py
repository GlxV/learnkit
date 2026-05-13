from pathlib import Path

from app.core.database.sqlite_storage import SQLiteStorage
from app.core.extractors.file_extractor import ExtractedFileResult, FileExtractionResult
from app.core.importer.ai_response_parser import AIResponseParser
from app.core.models.extracted_content import ExtractedContent
from app.core.models.imported_file import ImportedFile
from app.core.services.block_service import BlockService
from app.core.services.progress_service import ProgressService


def _extraction(file_name: str, text: str) -> FileExtractionResult:
    imported_file = ImportedFile(
        original_path=str(Path("materialteste") / file_name),
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


def _response(title: str, card_question: str, question_statement: str) -> str:
    return f"""# RESUMO

## Visao geral

{title}

# FLASHCARDS

## Card 1
Pergunta: {card_question}
Resposta: Resposta nova.

# PERGUNTAS

## Pergunta 1
Enunciado: {question_statement}
A) Alternativa A
B) Alternativa B
C) Alternativa C
D) Alternativa D
Gabarito: A
Explicacao: A alternativa A esta correta.
"""


def test_update_imported_package_replaces_materials_without_creating_new_block(
    tmp_path: Path,
) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Estrutura de Dados")
    module = storage.create_module(subject.slug, "Prova 1")
    service = BlockService(storage)
    progress_service = ProgressService(storage)

    created = service.save_imported_package(
        subject_ref=subject.slug,
        module_ref=module.slug,
        title="Pilhas",
        extraction=_extraction("pilhas_antigo.md", "texto antigo"),
        generated_prompt="prompt antigo",
        response_text=_response("Resumo antigo", "Card antigo?", "Pergunta antiga?"),
        parsed_response=AIResponseParser().parse(
            _response("Resumo antigo", "Card antigo?", "Pergunta antiga?")
        ),
    )
    old_card_id = created.flashcards[0].id
    old_question_id = created.questions[0].id
    progress_service.record_flashcard(created.id, old_card_id, "easy")
    progress_service.record_question(created.id, old_question_id, "A", "A")

    parsed_new = AIResponseParser().parse(
        _response("Resumo atualizado", "O que e uma pilha?", "Como uma pilha remove itens?")
    )
    updated = service.update_imported_package(
        block_id=created.id,
        extraction=_extraction("pilhas_novo.md", "texto novo extraido"),
        generated_prompt="prompt novo",
        response_text=_response(
            "Resumo atualizado",
            "O que e uma pilha?",
            "Como uma pilha remove itens?",
        ),
        parsed_response=parsed_new,
    )

    blocks = storage.list_blocks(subject.slug, module.slug)
    progress = progress_service.get_block_progress(created.id)

    assert [block.id for block in blocks] == [created.id]
    assert updated.id == created.id
    assert updated.title == "Pilhas"
    assert updated.extracted_content.text == "texto novo extraido"
    assert updated.generated_prompt == "prompt novo"
    assert updated.summary is not None
    assert "Resumo atualizado" in updated.summary.content
    assert [card.question for card in updated.flashcards] == ["O que e uma pilha?"]
    assert [question.statement for question in updated.questions] == [
        "Como uma pilha remove itens?"
    ]
    assert progress.flashcards_total == 1
    assert progress.questions_total == 1
    assert progress.flashcards_reviewed == 0
    assert progress.questions_answered == 0
    assert old_card_id not in progress.reviewed_flashcards
    assert old_question_id not in progress.answered_questions
