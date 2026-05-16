from __future__ import annotations

from pathlib import Path

import pytest

from app.application.use_cases.manage_study_summary import ManageStudySummaryUseCase
from app.core.database import SQLiteStorage
from app.core.models.summary import Summary


def test_manage_study_summary_updates_text_visual_and_preference(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Estrutura de Dados")
    module = storage.create_module(subject.slug, "Prova 1")
    block = storage.create_block(subject.slug, module.slug, "Pilhas")
    block.summary = Summary("Resumo antigo")
    storage.save_block(subject, module, block)

    updated = ManageStudySummaryUseCase(storage).update_summary(
        block.id,
        summary_markdown="# Pilhas\n\nLIFO.",
        summary_visual='{"title":"Pilhas","sections":[]}',
        preferred_summary_mode="visual",
    )
    _, _, loaded = storage.get_block_by_id(block.id)

    assert updated.preferred_summary_mode == "visual"
    assert loaded.summary is not None
    assert loaded.summary.content.startswith("# Pilhas")
    assert '"title": "Pilhas"' in loaded.summary_visual
    assert loaded.preferred_summary_mode == "visual"


def test_manage_study_summary_changes_preferred_mode_without_touching_content(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Banco de Dados")
    module = storage.create_module(subject.slug, "Revisao")
    block = storage.create_block(subject.slug, module.slug, "Normalizacao")
    block.summary = Summary("Resumo")
    block.summary_visual = '{"title":"Normalizacao","sections":[]}'
    block.preferred_summary_mode = "visual"
    storage.save_block(subject, module, block)

    updated = ManageStudySummaryUseCase(storage).set_preferred_mode(block.id, "text")

    assert updated.preferred_summary_mode == "text"
    assert updated.summary is not None
    assert updated.summary.content == "Resumo"
    assert '"title":"Normalizacao"' in updated.summary_visual


def test_manage_study_summary_rejects_invalid_visual_json(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Matematica")
    module = storage.create_module(subject.slug, "Geral")
    block = storage.create_block(subject.slug, module.slug, "Funcoes")

    with pytest.raises(ValueError, match="Resumo visual"):
        ManageStudySummaryUseCase(storage).update_summary(
            block.id,
            summary_markdown="Texto",
            summary_visual="{invalid",
            preferred_summary_mode="visual",
        )
