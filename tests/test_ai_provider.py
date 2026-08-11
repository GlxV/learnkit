from app.application.dto.ai_provider import ai_provider_options, get_ai_provider


def test_ai_provider_registry_contains_supported_external_providers() -> None:
    providers = ai_provider_options()

    assert [provider.key for provider in providers] == ["gemini", "chatgpt", "claude"]
    assert get_ai_provider("ChatGPT").url == "https://chatgpt.com/"
    assert get_ai_provider("missing").key == "gemini"
