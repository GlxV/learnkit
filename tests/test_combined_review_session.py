from __future__ import annotations

from pathlib import Path

import pytest

from app.application.query_services.study_session_query_service import StudySessionQueryService
from app.core.database import SQLiteStorage
from app.core.models.flashcard import Flashcard
from app.core.models.question import Question
from app.core.models.summary import Summary


def _create_combined_blocks(tmp_path: Path):
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Estrutura de Dados")
    module = storage.create_module(subject.slug, "Prova 1")
    arrays = storage.create_block(subject.slug, module.slug, "Arrays")
    arrays.summary = Summary("Acesso indexado e memoria contigua.")
    arrays.flashcards = [
        Flashcard("O que e acesso direto?", "Busca por indice."),
        Flashcard("O que e um array?", "Colecao contigua."),
    ]
    arrays.questions = [
        Question("Qual acesso usa indice?", {"A": "Array", "B": "Fila"}, "A"),
    ]
    storage.save_block(subject, module, arrays)

    lists = storage.create_block(subject.slug, module.slug, "Listas Ligadas")
    lists.summary = Summary("Nos conectados por ponteiros.")
    lists.flashcards = [
        Flashcard("O que e acesso direto?", "Busca por indice."),
        Flashcard("O que liga os nos?", "Ponteiros."),
    ]
    lists.questions = [
        Question("Qual acesso usa indice?", {"A": "Array", "B": "Fila"}, "A"),
        Question("Qual estrutura encadeia nos?", {"A": "Lista", "B": "Array"}, "A"),
    ]
    storage.save_block(subject, module, lists)
    return storage, arrays, lists


def test_combined_review_session_is_in_memory_and_retains_duplicate_origins(tmp_path: Path) -> None:
    storage, arrays, lists = _create_combined_blocks(tmp_path)

    session = StudySessionQueryService(storage).combined_review_session(
        [arrays.id, lists.id, arrays.id]
    )

    assert [block.block_title for block in session.blocks] == ["Arrays", "Listas Ligadas"]
    assert [summary.block_title for summary in session.summaries] == ["Arrays", "Listas Ligadas"]
    assert len(session.flashcards) == 3
    assert len(session.questions) == 2
    shared_card = next(
        card for card in session.flashcards if card.question == "O que e acesso direto?"
    )
    shared_question = next(
        question
        for question in session.questions
        if question.statement == "Qual acesso usa indice?"
    )
    assert {(origin.block_id, origin.item_id) for origin in shared_card.origins} == {
        (arrays.id, arrays.flashcards[0].id),
        (lists.id, lists.flashcards[0].id),
    }
    assert {(origin.block_id, origin.item_id) for origin in shared_question.origins} == {
        (arrays.id, arrays.questions[0].id),
        (lists.id, lists.questions[0].id),
    }
    assert storage.database_stats()["study_blocks"] == 2
    assert storage.list_pending_review_schedules() == []


def test_combined_review_session_requires_two_distinct_blocks(tmp_path: Path) -> None:
    storage, arrays, _lists = _create_combined_blocks(tmp_path)

    with pytest.raises(ValueError, match="dois blocos"):
        StudySessionQueryService(storage).combined_review_session([arrays.id, arrays.id])


def test_combined_review_session_includes_three_blocks_even_when_one_has_no_content(
    tmp_path: Path,
) -> None:
    storage, arrays, lists = _create_combined_blocks(tmp_path)
    subject, module, _block = storage.get_block_by_id(arrays.id)
    empty = storage.create_block(subject.slug, module.slug, "Pilhas")

    session = StudySessionQueryService(storage).combined_review_session(
        [arrays.id, lists.id, empty.id]
    )

    assert [block.block_title for block in session.blocks] == [
        "Arrays",
        "Listas Ligadas",
        "Pilhas",
    ]
    assert [summary.block_title for summary in session.summaries] == ["Arrays", "Listas Ligadas"]
    assert len(session.flashcards) == 3
    assert len(session.questions) == 2


def test_exam_review_filters_content_and_extracts_deduplicated_traps(tmp_path: Path) -> None:
    storage, arrays, lists = _create_combined_blocks(tmp_path)
    for block, text in (
        (arrays, "Não confunda acesso direto com busca sequencial."),
        (lists, "Não confunda acesso direto com busca sequencial."),
    ):
        subject, module, loaded = storage.get_block_by_id(block.id)
        loaded.summary_visual = (
            '{"title":"Revisao","sections":['
            '{"type":"exam_trap","title":"Pegadinha","text":"'
            + text
            + '"}]}'
        )
        storage.save_block(subject, module, loaded)

    session = StudySessionQueryService(storage).combined_review_session(
        [arrays.id, lists.id],
        include_summary=False,
        include_flashcards=False,
        include_questions=False,
        include_exam_traps=True,
    )

    assert session.summaries == []
    assert session.flashcards == []
    assert session.questions == []
    assert len(session.exam_traps) == 1
    assert len(session.exam_traps[0].origins) == 2


def test_exam_review_can_use_one_block_without_changing_combined_review_contract(tmp_path: Path) -> None:
    storage, arrays, _lists = _create_combined_blocks(tmp_path)

    session = StudySessionQueryService(storage).combined_review_session(
        [arrays.id],
        minimum_blocks=1,
    )

    assert [block.block_id for block in session.blocks] == [arrays.id]
