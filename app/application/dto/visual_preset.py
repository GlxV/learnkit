from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VisualTypography:
    title_size: int
    section_title_size: int
    body_size: int
    presentation_title_size: int
    presentation_section_title_size: int
    presentation_body_size: int


@dataclass(frozen=True, slots=True)
class VisualSpacing:
    content_margin: int
    presentation_margin: int
    section_gap: int
    presentation_gap: int
    panel_margin: int
    panel_gap: int
    hero_margin: int


@dataclass(frozen=True, slots=True)
class VisualCardStyle:
    radius: int
    border_width: int
    elevated_background_key: str


@dataclass(frozen=True, slots=True)
class VisualHeroStyle:
    radius: int
    minimum_height: int
    presentation_minimum_height: int


@dataclass(frozen=True, slots=True)
class VisualEmphasisStyle:
    accent_key: str
    secondary_accent_key: str
    warning_key: str
    danger_key: str
    success_key: str


@dataclass(frozen=True, slots=True)
class VisualPreset:
    key: str
    label: str
    palette: dict[str, str]
    typography: VisualTypography
    spacing: VisualSpacing
    card_style: VisualCardStyle
    hero_style: VisualHeroStyle
    emphasis_style: VisualEmphasisStyle
    prompt_guidance: str


_TYPOGRAPHY = VisualTypography(
    title_size=30,
    section_title_size=18,
    body_size=14,
    presentation_title_size=42,
    presentation_section_title_size=28,
    presentation_body_size=18,
)
_SPACING = VisualSpacing(
    content_margin=18,
    presentation_margin=34,
    section_gap=14,
    presentation_gap=20,
    panel_margin=22,
    panel_gap=10,
    hero_margin=26,
)


def _preset(
    key: str,
    label: str,
    palette: dict[str, str],
    guidance: str,
    *,
    typography: VisualTypography = _TYPOGRAPHY,
    spacing: VisualSpacing = _SPACING,
    card_radius: int = 16,
    hero_radius: int = 18,
    hero_height: int = 190,
    presentation_hero_height: int = 280,
) -> VisualPreset:
    return VisualPreset(
        key=key,
        label=label,
        palette=palette,
        typography=typography,
        spacing=spacing,
        card_style=VisualCardStyle(card_radius, 1, "card_alt"),
        hero_style=VisualHeroStyle(hero_radius, hero_height, presentation_hero_height),
        emphasis_style=VisualEmphasisStyle(
            accent_key="accent",
            secondary_accent_key="accent_2",
            warning_key="warning",
            danger_key="danger",
            success_key="success",
        ),
        prompt_guidance=guidance,
    )


VISUAL_PRESETS: dict[str, VisualPreset] = {
    "auto": _preset(
        "auto",
        "Auto",
        {
            "background": "#050B14",
            "card": "#091426",
            "card_alt": "#101B34",
            "card_soft": "#14213D",
            "border": "#263A60",
            "accent": "#60A5FA",
            "accent_2": "#8B5CF6",
            "accent_3": "#22D3EE",
            "warning": "#F59E0B",
            "danger": "#F87171",
            "success": "#34D399",
        },
        "Escolha uma composição equilibrada e adapte a hierarquia ao conteúdo.",
    ),
    "prova": _preset(
        "prova",
        "Prova",
        {
            "background": "#07111F",
            "card": "#0D1728",
            "card_alt": "#142033",
            "card_soft": "#18263A",
            "border": "#2B3B55",
            "accent": "#38BDF8",
            "accent_2": "#818CF8",
            "accent_3": "#FBBF24",
            "warning": "#F59E0B",
            "danger": "#FB7185",
            "success": "#22C55E",
        },
        "Use hierarquia limpa, comparações rápidas, memorização, pegadinhas e alertas de prova.",
        card_radius=16,
        hero_radius=20,
    ),
    "lab": _preset(
        "lab",
        "Lab",
        {
            "background": "#03130F",
            "card": "#071D17",
            "card_alt": "#0D2A21",
            "card_soft": "#12382C",
            "border": "#1F4D3D",
            "accent": "#2DD4BF",
            "accent_2": "#22C55E",
            "accent_3": "#A3E635",
            "warning": "#EAB308",
            "danger": "#F87171",
            "success": "#4ADE80",
        },
        "Organize processos, hipóteses, etapas, fórmulas e relações de causa e efeito como um laboratório.",
        card_radius=14,
        hero_radius=18,
    ),
    "neon": _preset(
        "neon",
        "Neon",
        {
            "background": "#050716",
            "card": "#0A1028",
            "card_alt": "#111A3D",
            "card_soft": "#172554",
            "border": "#334155",
            "accent": "#22D3EE",
            "accent_2": "#A78BFA",
            "accent_3": "#3B82F6",
            "warning": "#FACC15",
            "danger": "#FB7185",
            "success": "#34D399",
        },
        "Use contraste de azul, roxo e ciano com blocos curtos, destaque forte e leitura escaneável.",
        card_radius=18,
        hero_radius=24,
    ),
    "retro": _preset(
        "retro",
        "Retro",
        {
            "background": "#080D0A",
            "card": "#0D1511",
            "card_alt": "#132019",
            "card_soft": "#18291F",
            "border": "#33543F",
            "accent": "#86EFAC",
            "accent_2": "#FBBF24",
            "accent_3": "#5EEAD4",
            "warning": "#F59E0B",
            "danger": "#F87171",
            "success": "#22C55E",
        },
        "Use linguagem de terminal/CRT de forma sutil, mantendo contraste e organização acadêmica.",
        card_radius=10,
        hero_radius=12,
    ),
    "minimalista": _preset(
        "minimalista",
        "Minimalista",
        {
            "background": "#0A0F18",
            "card": "#111827",
            "card_alt": "#172033",
            "card_soft": "#1F2937",
            "border": "#334155",
            "accent": "#CBD5E1",
            "accent_2": "#60A5FA",
            "accent_3": "#94A3B8",
            "warning": "#FBBF24",
            "danger": "#F87171",
            "success": "#34D399",
        },
        "Prefira estrutura séria, clara e discreta, com poucos acentos e bastante espaço entre conceitos.",
        card_radius=12,
        hero_radius=14,
    ),
}


def get_visual_preset(value: object | None) -> VisualPreset:
    key = str(value or "auto").strip().lower()
    return VISUAL_PRESETS.get(key, VISUAL_PRESETS["auto"])


def is_visual_preset(value: object | None) -> bool:
    return str(value or "").strip().lower() in VISUAL_PRESETS


def visual_preset_options() -> list[tuple[str, str]]:
    return [(preset.label, preset.key) for preset in VISUAL_PRESETS.values()]
