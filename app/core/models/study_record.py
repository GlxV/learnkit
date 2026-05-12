from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.models.base import new_id, require_dict, utc_now


@dataclass(slots=True)
class StudyRecord:
    block_id: str
    item_type: str
    item_id: str
    result: str
    difficulty: str | None = None
    duration_seconds: int = 0
    created_at: str = field(default_factory=utc_now)
    id: str = field(default_factory=new_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "block_id": self.block_id,
            "item_type": self.item_type,
            "item_id": self.item_id,
            "result": self.result,
            "difficulty": self.difficulty,
            "duration_seconds": self.duration_seconds,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StudyRecord":
        safe = require_dict(data)
        return cls(
            id=str(safe.get("id", new_id())),
            block_id=str(safe.get("block_id", "")),
            item_type=str(safe.get("item_type", "")),
            item_id=str(safe.get("item_id", "")),
            result=str(safe.get("result", "")),
            difficulty=safe.get("difficulty"),
            duration_seconds=int(safe.get("duration_seconds", 0)),
            created_at=str(safe.get("created_at", utc_now())),
        )
