from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NavItem:
    key: str
    label: str
    icon: str


NAV_ITEMS = [
    NavItem("home", "Início", "home"),
    NavItem("subjects", "Matérias", "subjects"),
    NavItem("studies", "Estudos", "studies"),
    NavItem("flashcards", "Flashcards", "flashcards"),
    NavItem("questions", "Perguntas", "questions"),
    NavItem("progress", "Progresso", "progress"),
    NavItem("database", "Banco de Dados", "database"),
    NavItem("import", "Importação/IA", "import"),
    NavItem("settings", "Configurações", "settings"),
]
