from __future__ import annotations

from app.core.importer.ai_response_parser import AIResponseParser, ParsedAIResponse


class ParserService:
    def __init__(self, parser: AIResponseParser | None = None) -> None:
        self.parser = parser or AIResponseParser()

    def parse_markdown(self, response_markdown: str) -> ParsedAIResponse:
        return self.parser.parse(response_markdown)
