from pathlib import Path

import pytest

from app.core.database import SQLiteStorage
from app.core.models.summary import Summary
from app.core.services.block_service import BlockService


def test_update_summary_modes_persists_text_visual_and_preference(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db")
    subject = storage.create_subject("Estrutura de Dados")
    module = storage.create_module(subject.slug, "Prova 1")
    block = storage.create_block(subject.slug, module.slug, "Pilhas")
    block.summary = Summary("Resumo antigo")
    storage.save_block(subject, module, block)

    service = BlockService(storage)
    updated = service.update_summary_modes(
        block.id,
        summary_markdown="# Pilhas\n\nLIFO.",
        summary_visual='{"title":"Pilhas","sections":[{"type":"hero","title":"LIFO","text":"Ultimo a entrar."}]}',
        preferred_summary_mode="visual",
    )

    reopened = SQLiteStorage(tmp_path / "learnkit.db")
    _, _, loaded = reopened.get_block_by_id(block.id)

    assert updated.preferred_summary_mode == "visual"
    assert loaded.summary is not None
    assert loaded.summary.content.startswith("# Pilhas")
    assert '"title": "Pilhas"' in loaded.summary_visual
    assert loaded.preferred_summary_mode == "visual"


def test_update_summary_modes_rejects_invalid_visual_json(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db")
    subject = storage.create_subject("Banco de Dados")
    module = storage.create_module(subject.slug, "Revisão")
    block = storage.create_block(subject.slug, module.slug, "Normalização")

    service = BlockService(storage)

    with pytest.raises(ValueError, match="Resumo visual"):
        service.update_summary_modes(
            block.id,
            summary_markdown="Texto",
            summary_visual="{invalid",
            preferred_summary_mode="visual",
        )
