from pathlib import Path

from app.core.database.sqlite_storage import SQLiteStorage
from app.core.models.flashcard import Flashcard
from app.core.models.progress import StudyProgress
from app.core.models.question import Question
from app.core.models.summary import Summary


def test_sqlite_storage_persists_subject_module_block_materials_and_progress(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db")
    subject = storage.create_subject("Banco de Dados", "SQL e modelagem", icon="DB", color="#3B82F6")
    module = storage.create_module(subject.slug, "Prova 1")
    block = storage.create_block(subject.slug, module.slug, "Modelo Relacional")
    block.summary = Summary("## Resumo\n\nChaves e tabelas.")
    block.summary_visual = '{"title":"Modelo Relacional","sections":[]}'
    block.preferred_summary_mode = "visual"
    block.flashcards = [Flashcard("O que e chave primaria?", "Identificador unico.")]
    block.questions = [
        Question(
            statement="Qual alternativa define chave primaria?",
            alternatives={"A": "Identificador unico", "B": "Backup", "C": "Indice visual", "D": "Tabela"},
            correct_answer="A",
            explanation="A chave primaria identifica registros.",
        )
    ]
    storage.save_block(subject, module, block)
    progress = StudyProgress(reviewed_flashcards={block.flashcards[0].id: "easy"})
    storage.save_progress(block.id, progress)

    reopened = SQLiteStorage(tmp_path / "learnkit.db")
    subjects = reopened.list_subjects()
    _, _, loaded = reopened.get_block("Banco de Dados", "Prova 1", "Modelo Relacional")
    loaded_progress = reopened.get_progress(block.id)

    assert reopened.db_path.exists()
    assert len(subjects) == 1
    assert loaded.summary is not None
    assert loaded.summary.content.startswith("## Resumo")
    assert loaded.summary_visual.startswith("{")
    assert loaded.preferred_summary_mode == "visual"
    assert len(loaded.flashcards) == 1
    assert len(loaded.questions) == 1
    assert loaded_progress.reviewed_flashcards[block.flashcards[0].id] == "easy"


def test_sqlite_storage_cascades_delete_subject(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db")
    subject = storage.create_subject("Matematica")
    module = storage.create_module(subject.slug, "1o Bimestre")
    storage.create_block(subject.slug, module.slug, "Funcoes")

    storage.delete_subject(subject.slug)
    stats = storage.database_stats()

    assert stats["subjects"] == 0
    assert stats["modules"] == 0
    assert stats["study_blocks"] == 0
