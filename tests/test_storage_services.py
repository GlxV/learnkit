from pathlib import Path

from app.core.services.block_service import BlockService
from app.core.services.module_service import ModuleService
from app.core.services.study_service import StudyService
from app.core.services.subject_service import SubjectService
from app.core.storage.local_storage import LocalStorage


def test_create_subject_module_and_blocks_without_overwriting(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    subject_service = SubjectService(storage)
    module_service = ModuleService(storage)
    block_service = BlockService(storage)

    subject = subject_service.create_subject("Matematica", icon="Mx", color="#3B82F6")
    duplicated_subject = subject_service.create_subject("Matematica")
    module = module_service.create_module("Matematica", "1 Trimestre")
    block = block_service.create_block("Matematica", "1 Trimestre", "Funcoes do 1 grau")
    duplicated_block = block_service.create_block("Matematica", "1 Trimestre", "Funcoes do 1 grau")

    assert subject.name == "Matematica"
    assert subject.icon == "Mx"
    assert subject.color == "#3B82F6"
    assert duplicated_subject.slug == "matematica_2"
    assert module.name == "1 Trimestre"
    assert block.title == "Funcoes do 1 grau"
    assert duplicated_block.slug == "funcoes_do_1_grau_2"
    assert (tmp_path / "subjects" / "matematica" / "subject.json").exists()
    assert (
        tmp_path
        / "subjects"
        / "matematica"
        / "modules"
        / "1_trimestre"
        / "blocks"
        / "funcoes_do_1_grau"
        / "block.json"
    ).exists()


def test_study_service_aggregates_block_module_and_subject(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    subject_service = SubjectService(storage)
    module_service = ModuleService(storage)
    block_service = BlockService(storage)
    study_service = StudyService(storage)

    subject_service.create_subject("Banco de Dados")
    module_service.create_module("Banco de Dados", "Prova 1")
    block = block_service.create_block("Banco de Dados", "Prova 1", "Modelo Relacional")
    block_service.update_study_materials(
        block.id,
        summary_markdown="- Tabelas organizam dados.",
        flashcards_data=[
            {"question": "O que e tabela?", "answer": "Linhas e colunas."},
        ],
        questions_data=[
            {
                "statement": "Qual item organiza dados?",
                "alternatives": {
                    "A": "Tabela",
                    "B": "Janela",
                    "C": "Pasta",
                    "D": "Imagem",
                },
                "correct_answer": "A",
                "explanation": "Tabela organiza dados relacionais.",
            }
        ],
    )

    block_session = study_service.study_block("Banco de Dados", "Prova 1", "Modelo Relacional")
    module_session = study_service.study_module("Banco de Dados", "Prova 1")
    subject_session = study_service.study_subject("Banco de Dados")

    assert len(block_session.summaries) == 1
    assert len(module_session.flashcards) == 1
    assert len(subject_session.questions) == 1
    assert subject_session.scope == "subject"
