from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.models.base import new_id, require_dict, utc_now


@dataclass(slots=True)
class Subject:
    name: str
    slug: str
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    modules: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    id: str = field(default_factory=new_id)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "modules": self.modules,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Subject":
        safe = require_dict(data)
        return cls(
            id=str(safe.get("id", new_id())),
            name=str(safe.get("name", "")),
            slug=str(safe.get("slug", "")),
            description=safe.get("description"),
            icon=safe.get("icon"),
            color=safe.get("color"),
            created_at=str(safe.get("created_at", utc_now())),
            updated_at=str(safe.get("updated_at", utc_now())),
            modules=list(safe.get("modules", [])),
        )
