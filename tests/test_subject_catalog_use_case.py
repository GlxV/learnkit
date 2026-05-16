from __future__ import annotations

from pathlib import Path

from app.application.use_cases.manage_subject_catalog import ManageSubjectCatalogUseCase
from app.core.database import SQLiteStorage


def test_subject_catalog_use_case_creates_subject_with_initial_modules(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    use_case = ManageSubjectCatalogUseCase(storage)

    subject = use_case.create_subject(
        "Banco de Dados",
        "SQL e modelo relacional",
        color="#14B8A6",
        icon="database",
        initial_modules=["Geral", "Prova 1"],
    )

    modules = storage.list_modules(subject.slug)

    assert subject.name == "Banco de Dados"
    assert subject.color == "#14B8A6"
    assert subject.icon == "database"
    assert [module.name for module in modules] == ["Geral", "Prova 1"]


def test_subject_catalog_use_case_updates_subject_and_creates_module(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    use_case = ManageSubjectCatalogUseCase(storage)
    subject = use_case.create_subject("Fisica", "Descricao antiga")

    updated = use_case.update_subject(
        subject.id,
        "Fisica Aplicada",
        "Descricao nova",
        color="#EC4899",
        icon="atom",
    )
    module = use_case.create_module("Fisica Aplicada", "Cinematica", "Movimento")

    assert updated.id == subject.id
    assert updated.name == "Fisica Aplicada"
    assert updated.description == "Descricao nova"
    assert module.name == "Cinematica"
    assert storage.get_module("Fisica Aplicada", "Cinematica")[1].description == "Movimento"


def test_ui_data_provider_exposes_read_models_only(tmp_path: Path) -> None:
    from app.application.query_services.ui_data_provider import UIDataProvider

    provider = UIDataProvider(SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False))

    assert not hasattr(provider, "create_subject")
    assert not hasattr(provider, "update_subject")
    assert not hasattr(provider, "create_module")
