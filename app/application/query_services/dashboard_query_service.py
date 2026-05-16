from __future__ import annotations

from typing import Any

from app.application.dto.progress import ReviewDashboardDTO
from app.application.query_services.progress_query_service import ProgressQueryService
from app.core.models.progress import AggregateProgress
from app.core.storage.local_storage import LocalStorage


class DashboardQueryService:
    def __init__(self, storage: LocalStorage) -> None:
        self.progress_query_service = ProgressQueryService(storage)

    def global_stats(self) -> AggregateProgress:
        return self.progress_query_service.global_stats()

    def review_dashboard(self, subject_ref: str | None = None) -> dict[str, Any]:
        return self.progress_query_service.review_dashboard(subject_ref)

    def review_dashboard_dto(self, subject_ref: str | None = None) -> ReviewDashboardDTO:
        return self.progress_query_service.review_dashboard_dto(subject_ref)
