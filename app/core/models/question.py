from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.models.base import new_id, require_dict


@dataclass(slots=True)
class Question:
    statement: str
    alternatives: dict[str, str]
    correct_answer: str
    explanation: str | None = None
    id: str = field(default_factory=new_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "alternatives": self.alternatives,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Question":
        safe = require_dict(data)
        alternatives = safe.get("alternatives", {})
        if not isinstance(alternatives, dict):
            alternatives = {}
        return cls(
            id=str(safe.get("id", new_id())),
            statement=str(safe.get("statement", "")),
            alternatives={str(key): str(value) for key, value in alternatives.items()},
            correct_answer=str(safe.get("correct_answer", "")),
            explanation=safe.get("explanation"),
        )
