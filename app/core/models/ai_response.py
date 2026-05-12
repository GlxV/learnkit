from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.models.base import require_dict, utc_now


@dataclass(slots=True)
class AIResponse:
    raw_text: str
    imported_at: str = field(default_factory=utc_now)
    parsed_successfully: bool = False
    parser_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "imported_at": self.imported_at,
            "parsed_successfully": self.parsed_successfully,
            "parser_warnings": self.parser_warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AIResponse | None":
        if data is None:
            return None
        safe = require_dict(data)
        return cls(
            raw_text=str(safe.get("raw_text", "")),
            imported_at=str(safe.get("imported_at", utc_now())),
            parsed_successfully=bool(safe.get("parsed_successfully", False)),
            parser_warnings=list(safe.get("parser_warnings", [])),
        )
