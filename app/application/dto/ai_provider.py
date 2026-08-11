from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AIProviderDTO:
    key: str
    label: str
    url: str


AI_PROVIDER_OPTIONS: tuple[AIProviderDTO, ...] = (
    AIProviderDTO("gemini", "Gemini", "https://gemini.google.com/"),
    AIProviderDTO("chatgpt", "ChatGPT", "https://chatgpt.com/"),
    AIProviderDTO("claude", "Claude", "https://claude.ai/"),
)


def get_ai_provider(value: str | None) -> AIProviderDTO:
    normalized = (value or "").strip().lower()
    return next(
        (
            provider
            for provider in AI_PROVIDER_OPTIONS
            if provider.key == normalized
            or provider.label.lower() == normalized
            or provider.url.lower() == normalized
        ),
        AI_PROVIDER_OPTIONS[0],
    )


def ai_provider_options() -> tuple[AIProviderDTO, ...]:
    return AI_PROVIDER_OPTIONS
