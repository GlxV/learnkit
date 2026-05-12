from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.models.base import new_id, require_dict, utc_now


@dataclass(slots=True)
class Module:
    subject_id: str
    name: str
    slug: str
    description: str | None = None
    study_blocks: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    id: str = field(default_factory=new_id)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "subject_id": self.subject_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "study_blocks": self.study_blocks,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Module":
        safe = require_dict(data)
        return cls(
            id=str(safe.get("id", new_id())),
            subject_id=str(safe.get("subject_id", "")),
            name=str(safe.get("name", "")),
            slug=str(safe.get("slug", "")),
            description=safe.get("description"),
            created_at=str(safe.get("created_at", utc_now())),
            updated_at=str(safe.get("updated_at", utc_now())),
            study_blocks=list(safe.get("study_blocks", [])),
        )
