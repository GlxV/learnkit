from __future__ import annotations

from app.application.dto.visual_preset import (
    VISUAL_PRESETS,
    get_visual_preset,
    is_visual_preset,
    visual_preset_options,
)
from app.application.dto.visual_summary import parse_visual_summary
from app.core.models.extracted_content import ExtractedContent
from app.core.prompt.prompt_builder import PromptBuilder, PromptOptions


def test_visual_presets_are_registered_with_shared_rendering_contract() -> None:
    assert set(VISUAL_PRESETS) == {"auto", "prova", "lab", "neon", "retro", "minimalista"}
    assert [key for _label, key in visual_preset_options()] == list(VISUAL_PRESETS)
    for preset in VISUAL_PRESETS.values():
        assert preset.palette["background"]
        assert preset.typography.body_size > 0
        assert preset.spacing.section_gap > 0
        assert preset.card_style.radius > 0
        assert preset.hero_style.minimum_height > 0
        assert preset.prompt_guidance


def test_unknown_saved_style_keeps_compatibility_by_falling_back_to_auto() -> None:
    assert get_visual_preset("future-style").key == "auto"
    assert not is_visual_preset("future-style")
    parsed = parse_visual_summary(
        {"title": "Resumo antigo", "style": "future-style", "sections": []}
    )
    assert parsed is not None
    assert parsed["style"] == "auto"


def test_prompt_builder_uses_the_same_preset_guidance_as_the_renderer() -> None:
    preset = get_visual_preset("lab")
    prompt = PromptBuilder().build(
        "Biologia",
        "Prova",
        "Fungos",
        ExtractedContent(text="Hifas e micelio."),
        PromptOptions(visual_style="lab"),
    )

    assert preset.prompt_guidance in prompt
    assert '"style": "lab"' in prompt
