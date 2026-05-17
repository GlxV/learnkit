from __future__ import annotations

from PySide6.QtWidgets import QApplication, QComboBox, QFrame, QListView


BASE_THEME_VALUES = {
    "background": "#101412",
    "background_alt": "#0D1110",
    "surface": "#0D1110",
    "card": "#171C19",
    "card_alt": "#202721",
    "card_hover": "#252D27",
    "border": "#303A34",
    "border_hover": "#465449",
    "text": "#E8ECE7",
    "muted": "#AAB3AA",
    "weak": "#748077",
    "accent": "#6FA36B",
    "accent_hover": "#85BF7E",
    "accent_active": "#5F8F68",
    "accent_dark": "#27452D",
    "warning": "#C9A86A",
    "error": "#D17A7A",
    "success": "#7FBF7A",
    "secondary": "#85BF7E",
}

COLORS = {
    **BASE_THEME_VALUES,
    "surface_elevated": BASE_THEME_VALUES["card_alt"],
    "sidebar": BASE_THEME_VALUES["background_alt"],
    "blue": BASE_THEME_VALUES["accent"],
    "purple": BASE_THEME_VALUES["accent_active"],
    "purple_soft": BASE_THEME_VALUES["accent_hover"],
    "green": BASE_THEME_VALUES["success"],
    "amber": BASE_THEME_VALUES["warning"],
    "red": BASE_THEME_VALUES["error"],
}

SPACING = {
    "xs": 6,
    "sm": 10,
    "md": 16,
    "lg": 24,
    "xl": 32,
}


def apply_app_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setStyleSheet(build_theme_styles())


THEME_PRESETS = {
    "Graphite Green": BASE_THEME_VALUES,
    "LearnKit Dark": {
        "background": "#050B14",
        "background_alt": "#07111F",
        "surface": "#060F1C",
        "card": "#0B1626",
        "card_alt": "#101B2E",
        "card_hover": "#121F33",
        "border": "#223149",
        "border_hover": "#3B82F6",
        "text": "#F3F6FB",
        "muted": "#9BA8BA",
        "weak": "#697586",
        "accent": "#3B82F6",
        "accent_hover": "#60A5FA",
        "accent_active": "#2563EB",
        "accent_dark": "#1D2F55",
        "secondary": "#7C3AED",
    },
    "Midnight Indigo": {
        "background": "#050711",
        "background_alt": "#0A1024",
        "surface": "#090E1E",
        "card": "#10172A",
        "card_alt": "#151F36",
        "card_hover": "#1B2742",
        "border": "#26314A",
        "border_hover": "#8B5CF6",
        "text": "#F8FAFC",
        "muted": "#A7B0C2",
        "weak": "#7D8799",
        "accent": "#8B5CF6",
        "accent_hover": "#A78BFA",
        "accent_active": "#7C3AED",
        "accent_dark": "#312E81",
        "secondary": "#38BDF8",
    },
    "Graphite Focus": {
        "background": "#07090D",
        "background_alt": "#0D1117",
        "surface": "#0A0E14",
        "card": "#111827",
        "card_alt": "#172033",
        "card_hover": "#1F2937",
        "border": "#2A3446",
        "border_hover": "#64748B",
        "text": "#F4F7FB",
        "muted": "#A3ADBD",
        "weak": "#7B8494",
        "accent": "#60A5FA",
        "accent_hover": "#93C5FD",
        "accent_active": "#3B82F6",
        "accent_dark": "#1E3A5F",
        "secondary": "#94A3B8",
    },
    "Forest Lab": {
        "background": "#04110D",
        "background_alt": "#071A14",
        "surface": "#061611",
        "card": "#0C211A",
        "card_alt": "#123126",
        "card_hover": "#173D30",
        "border": "#1F3D33",
        "border_hover": "#2F6B52",
        "text": "#F1F8F4",
        "muted": "#A4B8AC",
        "weak": "#789083",
        "accent": "#22C55E",
        "accent_hover": "#4ADE80",
        "accent_active": "#16A34A",
        "accent_dark": "#14532D",
        "secondary": "#14B8A6",
    },
    "Ruby Night": {
        "background": "#12070B",
        "background_alt": "#1B0A12",
        "surface": "#160912",
        "card": "#24101A",
        "card_alt": "#311625",
        "card_hover": "#3A1A2C",
        "border": "#4A2335",
        "border_hover": "#EC4899",
        "text": "#FFF5F8",
        "muted": "#C9A6B5",
        "weak": "#9B7183",
        "accent": "#EC4899",
        "accent_hover": "#F472B6",
        "accent_active": "#DB2777",
        "accent_dark": "#831843",
        "secondary": "#F97316",
    },
}


def build_theme_styles(settings: dict[str, object] | None = None) -> str:
    values = theme_values(settings)
    style = GLOBAL_STYLES
    base = BASE_THEME_VALUES
    replacements = {
        base["background"]: values["background"],
        base["background_alt"]: values["background_alt"],
        base["surface"]: values["surface"],
        base["card"]: values["card"],
        base["card_alt"]: values["card_alt"],
        base["card_hover"]: values["card_hover"],
        base["border"]: values["border"],
        base["border_hover"]: values["border_hover"],
        base["text"]: values["text"],
        base["muted"]: values["muted"],
        base["weak"]: values["weak"],
        base["accent"]: values["accent"],
        base["accent_hover"]: values["accent_hover"],
        base["accent_active"]: values["accent_active"],
        base["accent_dark"]: values["accent_dark"],
        base["warning"]: values["warning"],
        base["error"]: values["error"],
        base["success"]: values["success"],
    }
    for old, new in replacements.items():
        if old != new:
            style = style.replace(str(old), str(new))
    return style


def theme_values(settings: dict[str, object] | None = None) -> dict[str, str]:
    settings = settings or {}
    preset_name = str(settings.get("theme_preset", settings.get("theme", "Graphite Green")))
    preset = THEME_PRESETS.get(preset_name, THEME_PRESETS["Graphite Green"])
    values = _complete_theme_values(dict(preset))
    custom = settings.get("custom_theme")
    if isinstance(custom, dict):
        for key in values:
            value = custom.get(key)
            if isinstance(value, str) and value.startswith("#") and len(value) in {4, 7}:
                values[key] = value
        secondary = custom.get("secondary")
        if isinstance(secondary, str) and secondary.startswith("#") and len(secondary) in {4, 7}:
            values["accent_hover"] = secondary
            values["border_hover"] = secondary
    return _complete_theme_values(values)


def _complete_theme_values(values: dict[str, str]) -> dict[str, str]:
    complete = dict(BASE_THEME_VALUES)
    complete.update(values)
    complete.setdefault("secondary", complete["accent_hover"])
    complete.setdefault("card_hover", complete["card_alt"])
    complete.setdefault("border_hover", complete["accent"])
    complete.setdefault("accent_hover", complete.get("secondary", complete["accent"]))
    complete.setdefault("accent_active", complete["accent"])
    complete.setdefault("accent_dark", complete["card_alt"])
    complete.setdefault("warning", BASE_THEME_VALUES["warning"])
    complete.setdefault("error", BASE_THEME_VALUES["error"])
    complete.setdefault("success", BASE_THEME_VALUES["success"])
    return complete


def apply_app_theme_settings(app: QApplication, settings: dict[str, object] | None = None) -> None:
    app.setStyle("Fusion")
    app.setStyleSheet(build_theme_styles(settings))


def polish_combo_box(combo: QComboBox) -> None:
    if not combo.property("learnkit_polished_combo"):
        combo.setView(QListView(combo))
        combo.setProperty("learnkit_polished_combo", True)
    view = combo.view()
    view.setFrameShape(QFrame.Shape.NoFrame)
    view.setContentsMargins(0, 0, 0, 0)
    view.viewport().setAutoFillBackground(True)
    view.window().setStyleSheet("background: transparent; border: 0; margin: 0; padding: 0;")
    view.setStyleSheet(
        f"""
        QListView {{
            background: {COLORS["card"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 10px;
            padding: 0;
            margin: 0;
            outline: 0;
        }}
        QListView::item {{
            min-height: 34px;
            padding: 8px 10px;
            border: 0;
            margin: 0;
        }}
        QListView::item:selected {{
            background: {COLORS["accent_dark"]};
            color: {COLORS["text"]};
        }}
        QListView::item:hover {{
            background: {COLORS["card_hover"]};
        }}
        """
    )


GLOBAL_STYLES = f"""
* {{
    font-family: "Segoe UI", "Inter", Arial, sans-serif;
    color: {COLORS["text"]};
    font-size: 14px;
}}

QMainWindow, QWidget#RootWindow {{
    background: {COLORS["background"]};
}}

QDialog, QDialog#NewSubjectDialog, QWidget#NewSubjectDialogContent {{
    background: {COLORS["background"]};
}}

QFrame#DialogActionBar {{
    background: {COLORS["surface"]};
    border-top: 1px solid {COLORS["border"]};
}}

QDialog QLabel, QWidget, QLabel {{
    background: transparent;
}}

QFrame#Sidebar {{
    background: {COLORS["sidebar"]};
    border-right: 1px solid {COLORS["border"]};
}}

QFrame#Topbar {{
    background: {COLORS["surface"]};
    border-bottom: 1px solid {COLORS["border"]};
}}

QFrame#Card, QFrame#StatCard, QFrame#SubjectCard, QFrame#ModuleCard,
QFrame#StudyBlockRow, QFrame#Panel, QFrame#FeatureCard {{
    background: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 16px;
}}

QFrame#FeatureCard, QFrame#HeroCard {{
    background: {COLORS["card_alt"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 16px;
}}

QFrame#SubjectCard:hover, QFrame#ModuleCard:hover, QFrame#StudyBlockRow:hover,
QFrame#FeatureCard:hover {{
    background: {COLORS["card_hover"]};
    border-color: {COLORS["border_hover"]};
}}

QLabel#Title {{
    font-size: 31px;
    font-weight: 750;
}}

QLabel#HeroTitle {{
    font-size: 22px;
    font-weight: 800;
}}

QLabel#PageTitle {{
    font-size: 24px;
    font-weight: 700;
}}

QLabel#SectionTitle {{
    font-size: 17px;
    font-weight: 750;
}}

QLabel#SmallTitle {{
    font-size: 15px;
    font-weight: 700;
}}

QLabel#Muted {{
    color: {COLORS["muted"]};
}}

QLabel#Weak {{
    color: {COLORS["weak"]};
    font-size: 12px;
}}

QLabel#Link {{
    color: {COLORS["accent_hover"]};
    font-weight: 600;
}}

QPushButton {{
    background: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    padding: 10px 13px;
    color: {COLORS["text"]};
    min-height: 18px;
}}

QPushButton:hover {{
    background: {COLORS["card_hover"]};
    border-color: {COLORS["border_hover"]};
}}

QPushButton:pressed {{
    background: {COLORS["card_alt"]};
    border-color: {COLORS["accent"]};
    padding-top: 11px;
    padding-bottom: 9px;
}}

QPushButton:disabled {{
    background: #121613;
    border-color: #222A25;
    color: {COLORS["weak"]};
}}

QPushButton#PrimaryButton {{
    background: {COLORS["accent_dark"]};
    border-color: {COLORS["accent"]};
    color: {COLORS["text"]};
    font-weight: 700;
}}

QPushButton#PrimaryButton:hover {{
    background: {COLORS["accent_active"]};
    border-color: {COLORS["accent_hover"]};
    color: #FFFFFF;
}}

QPushButton#PrimaryButton:pressed {{
    background: {COLORS["accent"]};
    border-color: {COLORS["accent_hover"]};
    color: #FFFFFF;
}}

QPushButton#PrimaryButton:disabled {{
    background: #182019;
    border-color: {COLORS["border"]};
    color: {COLORS["weak"]};
}}

QPushButton#GhostButton {{
    background: transparent;
    border-color: {COLORS["border"]};
}}

QPushButton#GhostButton:hover {{
    background: {COLORS["card_hover"]};
    border-color: {COLORS["border_hover"]};
}}

QPushButton#GhostButton:pressed {{
    background: {COLORS["card_alt"]};
    border-color: {COLORS["accent"]};
}}

QPushButton:checked {{
    background: {COLORS["accent_dark"]};
    border: 1px solid {COLORS["accent"]};
    color: {COLORS["text"]};
}}

QCheckBox {{
    spacing: 10px;
    color: {COLORS["muted"]};
    padding: 5px 0;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid {COLORS["border"]};
    background: {COLORS["card"]};
}}

QCheckBox::indicator:checked {{
    background: {COLORS["accent_dark"]};
    border-color: {COLORS["accent"]};
}}

QPushButton#SidebarItem {{
    background: transparent;
    border: 0;
    border-radius: 11px;
    padding: 12px 14px;
    text-align: left;
    color: {COLORS["muted"]};
    font-size: 15px;
}}

QPushButton#SidebarItem[active="true"] {{
    background: {COLORS["accent_dark"]};
    color: {COLORS["text"]};
    border-left: 3px solid {COLORS["accent"]};
}}

QPushButton#SidebarItem:hover {{
    background: {COLORS["card"]};
}}

QFrame#SidebarItemFrame {{
    background: transparent;
    border: 0;
    border-radius: 11px;
}}

QFrame#SidebarItemFrame[active="true"] {{
    background: {COLORS["accent_dark"]};
    border-left: 3px solid {COLORS["accent"]};
}}

QFrame#SidebarItemFrame:hover {{
    background: {COLORS["card"]};
}}

QToolButton#SidebarCollapseButton {{
    background: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    color: {COLORS["muted"]};
    font-size: 18px;
    font-weight: 800;
}}

QToolButton#SidebarCollapseButton:hover {{
    background: {COLORS["card_hover"]};
    border-color: {COLORS["border_hover"]};
    color: {COLORS["text"]};
}}

QToolButton#SidebarCollapseButton:pressed {{
    background: {COLORS["card_alt"]};
    border-color: {COLORS["accent"]};
}}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {{
    background: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 11px;
    padding: 10px 13px;
    color: {COLORS["text"]};
    selection-background-color: {COLORS["accent_active"]};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus {{
    border-color: {COLORS["accent"]};
    background: {COLORS["card_alt"]};
}}

QFrame#SearchBox {{
    background: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 11px;
}}

QFrame#SearchBox:hover {{
    border-color: {COLORS["border_hover"]};
}}

QLineEdit#SearchInput {{
    background: transparent;
    border: 0;
    padding: 0;
}}

QTextEdit, QPlainTextEdit {{
    line-height: 1.4;
}}

QComboBox {{
    background: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 11px;
    padding: 10px 38px 10px 13px;
    color: {COLORS["text"]};
    selection-background-color: {COLORS["accent_active"]};
    min-height: 20px;
}}

QComboBox:hover {{
    background: {COLORS["card_hover"]};
    border-color: {COLORS["border_hover"]};
}}

QComboBox:focus {{
    border-color: {COLORS["accent"]};
    background: {COLORS["card_alt"]};
}}

QComboBox:disabled {{
    background: #121613;
    border-color: #222A25;
    color: {COLORS["weak"]};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 34px;
    border-left: 1px solid {COLORS["border"]};
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
    background: {COLORS["card_alt"]};
}}

QComboBox::drop-down:hover {{
    background: {COLORS["card_hover"]};
}}

QComboBox::down-arrow {{
    image: url(app/ui/assets/combo_down.svg);
    width: 12px;
    height: 12px;
}}

QComboBox QAbstractItemView {{
    background: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    color: {COLORS["text"]};
    padding: 0;
    margin: 0;
    outline: 0;
    selection-background-color: {COLORS["accent_dark"]};
    selection-color: {COLORS["text"]};
}}

QComboBoxPrivateContainer {{
    background: transparent;
    border: 0;
    border-radius: 0;
    margin: 0;
    padding: 0;
}}

QComboBox QAbstractItemView::item {{
    min-height: 34px;
    padding: 8px 10px;
    border: 0;
    margin: 0;
    color: {COLORS["text"]};
}}

QComboBox QAbstractItemView::item:hover {{
    background: {COLORS["card_hover"]};
    color: {COLORS["text"]};
}}

QComboBox QAbstractItemView::item:selected {{
    background: {COLORS["accent_dark"]};
    color: {COLORS["text"]};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    background: {COLORS["card_alt"]};
    border-left: 1px solid {COLORS["border"]};
    width: 22px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: {COLORS["card_hover"]};
}}

QListWidget, QListView {{
    background: transparent;
    border: 0;
    outline: 0;
}}

QListWidget::item {{
    border: 0;
    padding: 4px;
}}

QListWidget::item:selected {{
    background: rgba(111, 163, 107, 0.18);
    border-radius: 10px;
}}

QFrame#FileListItem {{
    background: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
}}

QFrame#FileListItem:hover {{
    background: {COLORS["card_hover"]};
    border-color: {COLORS["border_hover"]};
}}

QFrame#Toast {{
    background: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
}}

QFrame#StepCard {{
    background: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 14px;
}}

QScrollArea {{
    border: 0;
    background: transparent;
}}

QScrollBar:vertical {{
    background: {COLORS["background"]};
    width: 10px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS["border"]};
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS["border_hover"]};
}}

QProgressBar {{
    background: {COLORS["card_alt"]};
    border: 0;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background: {COLORS["accent"]};
    border-radius: 5px;
}}

QTabWidget::pane {{
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
    top: -1px;
}}

QTabBar::tab {{
    background: transparent;
    color: {COLORS["muted"]};
    padding: 10px 18px;
    border-bottom: 2px solid transparent;
}}

QTabBar::tab:selected {{
    color: {COLORS["text"]};
    border-bottom-color: {COLORS["accent"]};
}}

QTableWidget {{
    background: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
    gridline-color: {COLORS["border"]};
}}

QHeaderView::section {{
    background: {COLORS["card_alt"]};
    border: 0;
    border-bottom: 1px solid {COLORS["border"]};
    color: {COLORS["muted"]};
    padding: 8px;
}}

QToolTip {{
    background: {COLORS["card_alt"]};
    border: 1px solid {COLORS["border_hover"]};
    color: {COLORS["text"]};
    padding: 6px 8px;
    border-radius: 6px;
}}
"""
