from __future__ import annotations

import json

from app.core.models.study_block import StudyBlock
from app.core.models.summary import Summary
from app.core.storage.local_storage import LocalStorage


class ManageStudySummaryUseCase:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage

    def update_summary(
        self,
        block_id: str,
        summary_markdown: str | None = None,
        summary_visual: str | None = None,
        preferred_summary_mode: str | None = None,
    ) -> StudyBlock:
        subject, module, block = self.storage.get_block_by_id(block_id)
        if summary_markdown is not None:
            block.summary = Summary(content=summary_markdown) if summary_markdown.strip() else None

        if summary_visual is not None:
            block.summary_visual = self._normalize_summary_visual(summary_visual)

        if preferred_summary_mode is not None:
            self._set_preferred_mode(block, preferred_summary_mode)
        elif block.preferred_summary_mode == "visual" and not block.summary_visual.strip():
            block.preferred_summary_mode = "text"

        block.touch()
        self.storage.save_block(subject, module, block)
        return block

    def set_preferred_mode(self, block_id: str, preferred_summary_mode: str) -> StudyBlock:
        subject, module, block = self.storage.get_block_by_id(block_id)
        self._set_preferred_mode(block, preferred_summary_mode)
        block.touch()
        self.storage.save_block(subject, module, block)
        return block

    def _set_preferred_mode(self, block: StudyBlock, mode: str) -> None:
        if mode not in {"text", "visual"}:
            raise ValueError("Modo de resumo invalido.")
        if mode == "visual" and not block.summary_visual.strip():
            raise ValueError("Resumo visual precisa existir para usar o modo visual.")
        block.preferred_summary_mode = mode

    def _normalize_summary_visual(self, value: str) -> str:
        raw = value.strip()
        if not raw:
            return ""
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Resumo visual possui JSON invalido: {exc.msg}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("Resumo visual precisa ser um objeto JSON.")
        return json.dumps(parsed, ensure_ascii=False, indent=2)
