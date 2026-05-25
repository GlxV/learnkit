from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.models.base import new_id, require_dict, utc_now


@dataclass(slots=True)
class ReviewSchedule:
    study_block_id: str
    subject_id: str
    module_id: str
    review_step: str
    scheduled_at: str
    status: str = "pending"
    completed_at: str | None = None
    created_at: str = field(default_factory=utc_now)
    id: str = field(default_factory=new_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "study_block_id": self.study_block_id,
            "subject_id": self.subject_id,
            "module_id": self.module_id,
            "review_step": self.review_step,
            "scheduled_at": self.scheduled_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReviewSchedule":
        safe = require_dict(data)
        return cls(
            id=str(safe.get("id", new_id())),
            study_block_id=str(safe.get("study_block_id", "")),
            subject_id=str(safe.get("subject_id", "")),
            module_id=str(safe.get("module_id", "")),
            review_step=str(safe.get("review_step", "")),
            scheduled_at=str(safe.get("scheduled_at", "")),
            completed_at=(
                str(safe["completed_at"]) if safe.get("completed_at") is not None else None
            ),
            status=str(safe.get("status", "pending")),
            created_at=str(safe.get("created_at", utc_now())),
        )
