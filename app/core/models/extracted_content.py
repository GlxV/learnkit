from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.models.base import require_dict


def _word_count(text: str) -> int:
    return len([word for word in text.split() if word.strip()])


@dataclass(slots=True)
class ExtractedContent:
    text: str = ""
    character_count: int | None = None
    word_count: int | None = None
    source_files: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.character_count is None:
            self.character_count = len(self.text)
        if self.word_count is None:
            self.word_count = _word_count(self.text)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "character_count": self.character_count,
            "word_count": self.word_count,
            "source_files": self.source_files,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ExtractedContent":
        safe = require_dict(data)
        return cls(
            text=str(safe.get("text", "")),
            character_count=int(safe.get("character_count", 0)),
            word_count=int(safe.get("word_count", 0)),
            source_files=list(safe.get("source_files", [])),
        )
