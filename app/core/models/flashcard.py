from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.models.base import new_id, require_dict


@dataclass(slots=True)
class Flashcard:
    question: str
    answer: str
    source: str | None = None
    id: str = field(default_factory=new_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Flashcard":
        safe = require_dict(data)
        return cls(
            id=str(safe.get("id", new_id())),
            question=str(safe.get("question", "")),
            answer=str(safe.get("answer", "")),
            source=safe.get("source"),
        )
