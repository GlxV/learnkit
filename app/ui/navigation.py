from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NavItem:
    key: str
    label: str
    icon: str
    developer_only: bool = False


NAV_ITEMS = [
    NavItem("home", "Início", "home"),
    NavItem("subjects", "Matérias", "subjects"),
    NavItem("studies", "Estudos", "studies"),
    NavItem("flashcards", "Flashcards", "flashcards"),
    NavItem("questions", "Perguntas", "questions"),
    NavItem("progress", "Progresso", "progress"),
    NavItem("database", "Banco de Dados", "database", developer_only=True),
    NavItem("import", "Importação/IA", "import"),
    NavItem("settings", "Configurações", "settings"),
]


def visible_nav_items(developer_mode: bool = False) -> list[NavItem]:
    return [item for item in NAV_ITEMS if developer_mode or not item.developer_only]
