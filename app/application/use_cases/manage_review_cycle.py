from __future__ import annotations

from datetime import datetime, timezone, tzinfo
from typing import Mapping

from app.application.dto.review_cycle import ReviewCycleActivationDTO
from app.core.models.review_schedule import ReviewSchedule
from app.core.storage.local_storage import LocalStorage
from app.domain.services.block_review_cycle_scheduler import BlockReviewCycleScheduler


class ManageReviewCycleUseCase:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage
        self.scheduler = BlockReviewCycleScheduler()

    def activate_cycle(
        self,
        block_id: str,
        *,
        studied_at: datetime | None = None,
        settings: Mapping[str, object] | None = None,
        automatic: bool = False,
        local_timezone: tzinfo | None = None,
    ) -> ReviewCycleActivationDTO:
        settings = settings or {}
        if automatic and not bool(settings.get("review_cycle_enabled", False)):
            return ReviewCycleActivationDTO(created=False, reason="automatic_disabled")
        if not self._supports_review_schedules():
            return ReviewCycleActivationDTO(created=False, reason="unsupported_storage")

        existing = self.storage.list_review_schedules(block_id)  # type: ignore[attr-defined]
        if existing:
            return ReviewCycleActivationDTO(
                created=False,
                schedules=existing,
                reason="already_exists",
            )
        subject, module, block = self.storage.get_block_by_id(block_id)
        try:
            schedules = self.scheduler.create_schedules(
                study_block_id=block.id,
                subject_id=subject.id,
                module_id=module.id,
                studied_at=studied_at or datetime.now(timezone.utc),
                settings=settings,
                local_timezone=local_timezone,
            )
        except ValueError as exc:
            if automatic:
                reason = (
                    "no_enabled_steps"
                    if "pelo menos uma etapa" in str(exc)
                    else "invalid_settings"
                )
                return ReviewCycleActivationDTO(created=False, reason=reason)
            raise
        stored = self.storage.create_review_schedules(schedules)  # type: ignore[attr-defined]
        return ReviewCycleActivationDTO(created=True, schedules=stored)

    def complete_review(
        self,
        schedule_id: str,
        *,
        completed_at: datetime | None = None,
    ) -> ReviewSchedule:
        return self._set_final_status(schedule_id, "done", completed_at)

    def skip_review(
        self,
        schedule_id: str,
        *,
        completed_at: datetime | None = None,
    ) -> ReviewSchedule:
        return self._set_final_status(schedule_id, "skipped", completed_at)

    def _set_final_status(
        self,
        schedule_id: str,
        status: str,
        completed_at: datetime | None,
    ) -> ReviewSchedule:
        if not self._supports_review_schedules():
            raise ValueError("Ciclo de Revisão requer armazenamento SQLite.")
        timestamp = (completed_at or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        return self.storage.update_review_schedule_status(  # type: ignore[attr-defined]
            schedule_id,
            status,
            completed_at=timestamp,
        )

    def _supports_review_schedules(self) -> bool:
        return all(
            hasattr(self.storage, method)
            for method in (
                "list_review_schedules",
                "create_review_schedules",
                "update_review_schedule_status",
            )
        )
