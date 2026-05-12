from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.models.base import new_id, require_dict


@dataclass(slots=True)
class Summary:
    content: str
    format: str = "markdown"
    id: str = field(default_factory=new_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "format": self.format,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Summary | None":
        if data is None:
            return None
        safe = require_dict(data)
        return cls(
            id=str(safe.get("id", new_id())),
            content=str(safe.get("content", "")),
            format=str(safe.get("format", "markdown")),
        )
