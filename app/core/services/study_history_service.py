from __future__ import annotations

import json
from dataclasses import dataclass

from app.core.models.study_record import StudyRecord
from app.core.storage.local_storage import LocalStorage


@dataclass(slots=True)
class StudyStats:
    total_reviews: int
    correct: int
    incorrect: int
    skipped: int
    accuracy: float
    total_duration_seconds: int


class StudyHistoryService:
    VALID_RESULTS = {"correct", "incorrect", "skipped", "neutral"}

    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage
        self.history_path = storage.base_path / "study_history.json"

    def record_result(
        self,
        block_id: str,
        item_type: str,
        item_id: str,
        result: str,
        difficulty: str | None = None,
        duration_seconds: int = 0,
    ) -> StudyRecord:
        normalized_result = result.strip().lower()
        if normalized_result not in self.VALID_RESULTS:
            raise ValueError(
                "Resultado invalido. Use correct, incorrect, skipped ou neutral."
            )
        if duration_seconds < 0:
            raise ValueError("A duracao nao pode ser negativa.")

        record = StudyRecord(
            block_id=block_id,
            item_type=item_type,
            item_id=item_id,
            result=normalized_result,
            difficulty=difficulty,
            duration_seconds=duration_seconds,
        )
        records = self.list_records()
        records.append(record)
        self._save(records)
        return record

    def list_records(self, block_id: str | None = None) -> list[StudyRecord]:
        if not self.history_path.exists():
            return []
        data = json.loads(self.history_path.read_text(encoding="utf-8"))
        records = [StudyRecord.from_dict(item) for item in data]
        if block_id is None:
            return records
        return [record for record in records if record.block_id == block_id]

    def get_stats(self, block_id: str | None = None) -> StudyStats:
        records = self.list_records(block_id)
        correct = len([record for record in records if record.result == "correct"])
        incorrect = len([record for record in records if record.result == "incorrect"])
        skipped = len([record for record in records if record.result == "skipped"])
        answered = correct + incorrect
        return StudyStats(
            total_reviews=len(records),
            correct=correct,
            incorrect=incorrect,
            skipped=skipped,
            accuracy=(correct / answered) if answered else 0.0,
            total_duration_seconds=sum(record.duration_seconds for record in records),
        )

    def _save(self, records: list[StudyRecord]) -> None:
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_path.write_text(
            json.dumps([record.to_dict() for record in records], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
