from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.models.base import new_id, require_dict, utc_now


@dataclass(slots=True)
class ImportedFile:
    original_path: str
    file_name: str
    file_type: str
    file_size: int
    extraction_status: str
    error_message: str | None = None
    page_count: int | None = None
    slide_count: int | None = None
    extraction_warnings: list[str] = field(default_factory=list)
    imported_at: str = field(default_factory=utc_now)
    id: str = field(default_factory=new_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "original_path": self.original_path,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "imported_at": self.imported_at,
            "extraction_status": self.extraction_status,
            "error_message": self.error_message,
            "page_count": self.page_count,
            "slide_count": self.slide_count,
            "extraction_warnings": self.extraction_warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImportedFile":
        safe = require_dict(data)
        return cls(
            id=str(safe.get("id", new_id())),
            original_path=str(safe.get("original_path", "")),
            file_name=str(safe.get("file_name", "")),
            file_type=str(safe.get("file_type", "")),
            file_size=int(safe.get("file_size", 0)),
            imported_at=str(safe.get("imported_at", utc_now())),
            extraction_status=str(safe.get("extraction_status", "unknown")),
            error_message=safe.get("error_message"),
            page_count=safe.get("page_count"),
            slide_count=safe.get("slide_count"),
            extraction_warnings=list(safe.get("extraction_warnings", [])),
        )
