from __future__ import annotations

from app.core.storage.local_storage import LocalStorage

SearchResult = tuple[str, str, dict[str, str]]


class SearchQueryService:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage

    def search(self, query: str, limit: int = 50) -> list[SearchResult]:
        normalized = query.strip().casefold()
        if not normalized:
            return []

        results: list[SearchResult] = []
        for subject in self.storage.list_subjects():
            if normalized in subject.name.casefold():
                results.append((subject.name, "Matéria", {"kind": "subject", "subject": subject.name}))
            if subject.description and normalized in subject.description.casefold():
                results.append((subject.name, "Resumo da matéria", {"kind": "subject", "subject": subject.name}))
            for module in self.storage.list_modules(subject.slug):
                if normalized in module.name.casefold():
                    results.append(
                        (
                            module.name,
                            f"Módulo em {subject.name}",
                            {"kind": "module", "subject": subject.name, "module": module.name},
                        )
                    )
                for block in self.storage.list_blocks(subject.slug, module.slug):
                    block_target = {"kind": "block", "block_id": block.id}
                    if normalized in block.title.casefold():
                        results.append((block.title, f"Bloco em {subject.name} > {module.name}", block_target))
                    if block.summary and normalized in block.summary.content.casefold():
                        results.append((block.title, f"Resumo em {subject.name} > {module.name}", block_target))
                    for card in block.flashcards:
                        haystack = f"{card.question} {card.answer}".casefold()
                        if normalized in haystack:
                            results.append(
                                (
                                    card.question[:90],
                                    f"Flashcard em {block.title}",
                                    {"kind": "flashcard", "block_id": block.id},
                                )
                            )
                    for question in block.questions:
                        haystack = " ".join([question.statement, *question.alternatives.values()]).casefold()
                        if normalized in haystack:
                            results.append(
                                (
                                    question.statement[:90],
                                    f"Pergunta em {block.title}",
                                    {"kind": "question", "block_id": block.id},
                                )
                            )
        return results[:limit]
