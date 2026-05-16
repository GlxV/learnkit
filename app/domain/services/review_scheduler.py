from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


class ReviewScheduler:
    def next_review(self, current_review: dict[str, Any] | None, status: str) -> dict[str, Any]:
        current = current_review if isinstance(current_review, dict) else {}
        now = datetime.now(timezone.utc)
        previous_interval = int(current.get("interval_days", 0) or 0)
        ease = float(current.get("ease_factor", 2.5) or 2.5)
        times = int(current.get("times_reviewed", 0) or 0)

        if status == "again":
            interval_days = 0
            ease = max(1.3, ease - 0.2)
        elif status == "hard":
            interval_days = 1 if previous_interval < 1 else max(1, round(previous_interval * 1.2))
            ease = max(1.3, ease - 0.15)
        elif status == "good":
            interval_days = 1 if times == 0 else max(previous_interval + 1, round(previous_interval * ease))
        elif status == "easy":
            interval_days = 4 if times == 0 else max(previous_interval + 2, round(previous_interval * ease * 1.3))
            ease = min(3.2, ease + 0.15)
        else:
            interval_days = previous_interval

        due_at = now if interval_days == 0 else now + timedelta(days=interval_days)
        reviewed_at = now.isoformat()
        return {
            "status": status,
            "times_reviewed": times + 1,
            "ease_factor": round(ease, 2),
            "interval_days": interval_days,
            "last_reviewed_at": reviewed_at,
            "due_at": reviewed_at if interval_days == 0 else due_at.isoformat(),
        }
