from __future__ import annotations

from pathlib import Path

from app.core.database import SQLiteStorage
from app.core.models.flashcard import Flashcard
from app.core.models.imported_file import ImportedFile
from app.core.models.progress import StudyProgress
from app.core.models.question import Question
from app.core.models.summary import Summary


def test_subject_module_repositories_back_storage_facade(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Matematica")
    module = storage.create_module(subject.slug, "Prova 1")

    subject_rows = storage.subject_repository.list_rows()
    subject_row = storage.subject_repository.get_row("Matematica")
    module_rows = storage.module_repository.list_rows(subject.id)
    module_row = storage.module_repository.get_row(subject.id, "Prova 1")

    assert [row["id"] for row in subject_rows] == [subject.id]
    assert subject_row is not None
    assert subject_row["slug"] == subject.slug
    assert [row["id"] for row in module_rows] == [module.id]
    assert module_row is not None
    assert module_row["slug"] == module.slug
    assert storage.subject_repository.module_slugs(subject.id) == [module.slug]


def test_block_repository_persists_material_rows_for_storage_facade(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Computacao")
    module = storage.create_module(subject.slug, "Estruturas")
    block = storage.create_block(subject.slug, module.slug, "Pilhas")
    block.flashcards = [Flashcard("O que e pilha?", "LIFO")]
    block.questions = [
        Question(
            statement="Qual estrutura usa LIFO?",
            alternatives={"A": "Pilha", "B": "Fila", "C": "Grafo", "D": "Hash"},
            correct_answer="A",
        )
    ]
    storage.save_block(subject, module, block)

    rows = storage.block_repository.list_rows(module.id)
    card_rows = storage.block_repository.flashcard_rows(block.id)
    question_rows = storage.block_repository.question_rows(block.id)

    assert [row["id"] for row in rows] == [block.id]
    assert card_rows[0]["question"] == "O que e pilha?"
    assert question_rows[0]["question_text"] == "Qual estrutura usa LIFO?"


def test_repositories_return_domain_models_for_storage_facade(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Historia", description="ENEM")
    module = storage.create_module(subject.slug, "Brasil Republica")
    block = storage.create_block(subject.slug, module.slug, "Era Vargas")
    block.imported_files = [
        ImportedFile(
            original_path="C:/temp/vargas.md",
            file_name="vargas.md",
            file_type="md",
            file_size=42,
            extraction_status="success",
        )
    ]
    block.summary = Summary("Resumo textual")
    block.summary_visual = '{"nodes":[]}'
    block.flashcards = [Flashcard("Quem foi Vargas?", "Presidente do Brasil")]
    block.questions = [
        Question(
            statement="Em que ano comeca o Estado Novo?",
            alternatives={"A": "1930", "B": "1937", "C": "1945", "D": "1954"},
            correct_answer="B",
            explanation="O Estado Novo foi instaurado em 1937.",
        )
    ]
    storage.save_block(subject, module, block)

    subjects = storage.subject_repository.list_subjects()
    found_subject = storage.subject_repository.get_subject("Historia")
    modules = storage.module_repository.list_modules(subject.id)
    found_module = storage.module_repository.get_module(subject.id, "Brasil Republica")
    blocks = storage.block_repository.list_blocks(module.id, subject.id)
    found_block = storage.block_repository.get_block(module.id, "Era Vargas", subject.id)
    block_context = storage.block_repository.get_block_context(block.id)

    assert subjects[0].modules == [module.slug]
    assert found_subject is not None
    assert found_subject.id == subject.id
    assert modules[0].study_blocks == [block.slug]
    assert found_module is not None
    assert found_module.id == module.id
    assert blocks[0].summary is not None
    assert blocks[0].summary.content == "Resumo textual"
    assert blocks[0].summary_visual == '{"nodes":[]}'
    assert blocks[0].flashcards[0].question == "Quem foi Vargas?"
    assert blocks[0].questions[0].correct_answer == "B"
    assert found_block is not None
    assert found_block.imported_files[0].file_name == "vargas.md"
    assert block_context is not None
    context_subject, context_module, context_block = block_context
    assert context_subject.id == subject.id
    assert context_module.id == module.id
    assert context_block.id == block.id


def test_progress_repository_persists_progress_and_material_state(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Computacao")
    module = storage.create_module(subject.slug, "Estruturas")
    block = storage.create_block(subject.slug, module.slug, "Filas")
    block.flashcards = [Flashcard("O que e fila?", "FIFO")]
    storage.save_block(subject, module, block)
    card_id = block.flashcards[0].id

    storage.save_progress(
        block.id,
        StudyProgress(
            flashcards_total=1,
            flashcards_reviewed=1,
            reviewed_flashcards={card_id: "easy"},
            flashcard_reviews={
                card_id: {
                    "status": "easy",
                    "times_reviewed": 2,
                    "last_reviewed_at": "2026-01-01T00:00:00+00:00",
                }
            },
        ),
    )

    progress_row = storage.progress_repository.get_row(block.id)
    progress = storage.progress_repository.get_progress(block.id)
    card_rows = storage.block_repository.flashcard_rows(block.id)

    assert progress_row is not None
    assert progress_row["reviewed_flashcards"] == 1
    assert progress.flashcards_reviewed == 1
    assert progress.flashcard_reviews[card_id]["times_reviewed"] == 2
    assert card_rows[0]["status"] == "easy"
    assert card_rows[0]["times_reviewed"] == 2
