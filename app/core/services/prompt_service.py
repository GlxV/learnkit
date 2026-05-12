from __future__ import annotations

from app.core.prompt.prompt_builder import PromptBuilder, PromptOptions
from app.core.storage.local_storage import LocalStorage


class PromptService:
    def __init__(self, storage: LocalStorage, prompt_builder: PromptBuilder | None = None) -> None:
        self.storage = storage
        self.prompt_builder = prompt_builder or PromptBuilder()

    def generate_for_block(
        self,
        subject_ref: str,
        module_ref: str,
        block_ref: str,
        options: PromptOptions | None = None,
    ) -> str:
        subject, module, block = self.storage.get_block(subject_ref, module_ref, block_ref)
        prompt = self.prompt_builder.build(subject.name, module.name, block.title, block.extracted_content, options)
        block.generated_prompt = prompt
        block.touch()
        self.storage.save_block(subject, module, block)
        return prompt
