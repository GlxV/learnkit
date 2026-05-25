from __future__ import annotations

from datetime import datetime, timedelta, timezone, tzinfo
from typing import Mapping

from app.core.models.review_schedule import ReviewSchedule


class BlockReviewCycleScheduler:
    STEP_DELAYS = (
        ("1h", timedelta(hours=1)),
        ("24h", timedelta(days=1)),
        ("7d", timedelta(days=7)),
        ("30d", timedelta(days=30)),
    )
    PREFERRED_TIME_STEPS = {"24h", "7d", "30d"}

    def create_schedules(
        self,
        *,
        study_block_id: str,
        subject_id: str,
        module_id: str,
        studied_at: datetime,
        settings: Mapping[str, object] | None = None,
        local_timezone: tzinfo | None = None,
    ) -> list[ReviewSchedule]:
        settings = settings or {}
        timezone_for_schedule = local_timezone or datetime.now().astimezone().tzinfo or timezone.utc
        studied_local = self._aware_datetime(studied_at, timezone_for_schedule).astimezone(
            timezone_for_schedule
        )
        preferred_time = self._preferred_time(settings)
        enabled_steps = [
            step
            for step, _delay in self.STEP_DELAYS
            if bool(settings.get(f"review_step_{step}_enabled", True))
        ]
        if not enabled_steps:
            raise ValueError("Ative pelo menos uma etapa do Ciclo de Revisão.")

        schedules: list[ReviewSchedule] = []
        for step, delay in self.STEP_DELAYS:
            if step not in enabled_steps:
                continue
            scheduled_local = studied_local + delay
            if preferred_time is not None and step in self.PREFERRED_TIME_STEPS:
                scheduled_local = scheduled_local.replace(
                    hour=preferred_time[0],
                    minute=preferred_time[1],
                    second=0,
                    microsecond=0,
                )
            schedules.append(
                ReviewSchedule(
                    study_block_id=study_block_id,
                    subject_id=subject_id,
                    module_id=module_id,
                    review_step=step,
                    scheduled_at=scheduled_local.astimezone(timezone.utc).isoformat(),
                )
            )
        return schedules

    def _preferred_time(self, settings: Mapping[str, object]) -> tuple[int, int] | None:
        raw = str(settings.get("preferred_review_time", "") or "").strip()
        if not raw:
            return None
        try:
            parsed = datetime.strptime(raw, "%H:%M")
        except ValueError as exc:
            raise ValueError("Horário preferido inválido. Use HH:mm.") from exc
        return parsed.hour, parsed.minute

    def _aware_datetime(self, value: datetime, local_timezone: tzinfo) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=local_timezone)
        return value
