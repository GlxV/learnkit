from __future__ import annotations

from app.core.models.extracted_content import ExtractedContent
from app.core.prompt.prompt_builder import PromptBuilder, PromptOptions


class GeneratePromptUseCase:
    def __init__(self, prompt_builder: PromptBuilder | None = None) -> None:
        self.prompt_builder = prompt_builder or PromptBuilder()

    def execute(
        self,
        subject_name: str,
        module_name: str,
        block_title: str,
        extracted_content: ExtractedContent,
        options: PromptOptions | None = None,
    ) -> str:
        return self.prompt_builder.build(
            subject_name=subject_name,
            module_name=module_name,
            block_title=block_title,
            extracted_content=extracted_content,
            options=options,
        )
