from __future__ import annotations

from PySide6.QtWidgets import QApplication, QComboBox, QFrame, QListView


COLORS = {
    "background": "#06101D",
    "surface": "#081423",
    "sidebar": "#050D19",
    "card": "#0D1828",
    "card_hover": "#121F33",
    "border": "#223149",
    "text": "#F3F6FB",
    "muted": "#9BA8BA",
    "weak": "#697586",
    "blue": "#3B82F6",
    "purple": "#7C3AED",
    "purple_soft": "#8B5CF6",
    "green": "#22C55E",
    "amber": "#F59E0B",
    "red": "#EF4444",
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
    "LearnKit Dark": {
        "background": "#050B14",
        "background_alt": "#07111F",
        "surface": "#060F1C",
        "card": "#0B1626",
        "card_alt": "#101B2E",
        "border": "#223149",
        "text": "#F3F6FB",
        "muted": "#9BA8BA",
        "accent": "#3B82F6",
        "secondary": "#7C3AED",
    },
    "Midnight Indigo": {
        "background": "#050711",
        "background_alt": "#0A1024",
        "surface": "#090E1E",
        "card": "#10172A",
        "card_alt": "#151F36",
        "border": "#26314A",
        "text": "#F8FAFC",
        "muted": "#A7B0C2",
        "accent": "#8B5CF6",
        "secondary": "#38BDF8",
    },
    "Graphite Focus": {
        "background": "#07090D",
        "background_alt": "#0D1117",
        "surface": "#0A0E14",
        "card": "#111827",
        "card_alt": "#172033",
        "border": "#2A3446",
        "text": "#F4F7FB",
        "muted": "#A3ADBD",
        "accent": "#60A5FA",
        "secondary": "#94A3B8",
    },
    "Forest Lab": {
        "background": "#04110D",
        "background_alt": "#071A14",
        "surface": "#061611",
        "card": "#0C211A",
        "card_alt": "#123126",
        "border": "#1F3D33",
        "text": "#F1F8F4",
        "muted": "#A4B8AC",
        "accent": "#22C55E",
        "secondary": "#14B8A6",
    },
    "Ruby Night": {
        "background": "#12070B",
        "background_alt": "#1B0A12",
        "surface": "#160912",
        "card": "#24101A",
        "card_alt": "#311625",
        "border": "#4A2335",
        "text": "#FFF5F8",
        "muted": "#C9A6B5",
        "accent": "#EC4899",
        "secondary": "#F97316",
    },
}


def build_theme_styles(settings: dict[str, object] | None = None) -> str:
    values = theme_values(settings)
    style = GLOBAL_STYLES
    replacements = {
        "#050B14": values["background"],
        "#07111F": values["background_alt"],
        "#060F1C": values["surface"],
        "#0B1626": values["card"],
        "#101B2E": values["card_alt"],
        "#223149": values["border"],
        COLORS["text"]: values["text"],
        COLORS["muted"]: values["muted"],
        COLORS["blue"]: values["accent"],
        COLORS["purple"]: values["secondary"],
        COLORS["purple_soft"]: values["secondary"],
    }
    for old, new in replacements.items():
        style = style.replace(old, str(new))
    return style


def theme_values(settings: dict[str, object] | None = None) -> dict[str, str]:
    settings = settings or {}
    preset_name = str(settings.get("theme_preset", settings.get("theme", "LearnKit Dark")))
    values = dict(THEME_PRESETS.get(preset_name, THEME_PRESETS["LearnKit Dark"]))
    custom = settings.get("custom_theme")
    if isinstance(custom, dict):
        for key in values:
            value = custom.get(key)
            if isinstance(value, str) and value.startswith("#") and len(value) in {4, 7}:
                values[key] = value
    return values


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
        """
        QListView {
            background: #0B1626;
            border: 1px solid #223149;
            border-radius: 10px;
            padding: 0;
            margin: 0;
            outline: 0;
        }
        QListView::item {
            min-height: 34px;
            padding: 8px 10px;
            border: 0;
            margin: 0;
        }
        QListView::item:selected {
            background: #7C3AED;
            color: #FFFFFF;
        }
        QListView::item:hover {
            background: #12213A;
        }
        """
    )


GLOBAL_STYLES = f"""
* {{
    font-family: "Segoe UI", "Inter", Arial, sans-serif;
    color: {COLORS["text"]};
    font-size: 14px;
}}

QMainWindow, QWidget#RootWindow {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #050B14, stop:0.45 #07111F, stop:1 #050B14);
}}

QDialog {{
    background: #050B14;
}}

QDialog QLabel {{
    background: transparent;
}}

QWidget {{
    background: transparent;
}}

QLabel {{
    background: transparent;
}}

QFrame#Sidebar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #050B14, stop:1 #08111F);
    border-right: 1px solid {COLORS["border"]};
}}

QFrame#Topbar {{
    background: #060F1C;
    border-bottom: 1px solid {COLORS["border"]};
}}

QFrame#Card, QFrame#StatCard, QFrame#SubjectCard, QFrame#ModuleCard,
QFrame#StudyBlockRow, QFrame#Panel, QFrame#FeatureCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #101B2E, stop:1 #0B1626);
    border: 1px solid {COLORS["border"]};
    border-radius: 16px;
}}

QFrame#HeroCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #101B31, stop:0.55 #0C1829, stop:1 #0A1423);
    border: 1px solid {COLORS["border"]};
    border-radius: 16px;
}}

QFrame#SubjectCard:hover, QFrame#ModuleCard:hover, QFrame#StudyBlockRow:hover {{
    background: {COLORS["card_hover"]};
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
    color: #60A5FA;
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
    border-color: {COLORS["blue"]};
}}

QPushButton:pressed {{
    background: #081322;
    border-color: {COLORS["purple_soft"]};
    padding-top: 11px;
    padding-bottom: 9px;
}}

QPushButton:disabled {{
    background: #08111D;
    border-color: #162235;
    color: #536176;
}}

QPushButton#PrimaryButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS["blue"]}, stop:1 {COLORS["purple"]});
    border-color: {COLORS["purple_soft"]};
    color: white;
    font-weight: 700;
}}

QPushButton#PrimaryButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2563EB, stop:1 #6D28D9);
    border-color: #A78BFA;
}}

QPushButton#PrimaryButton:pressed {{
    background: #5B21B6;
    border-color: #C4B5FD;
}}

QPushButton#PrimaryButton:disabled {{
    background: #132033;
    border-color: #1B2A42;
    color: #65758B;
}}

QPushButton#GhostButton {{
    background: transparent;
    border-color: {COLORS["border"]};
}}

QPushButton#GhostButton:hover {{
    background: #101B31;
    border-color: {COLORS["blue"]};
}}

QPushButton#GhostButton:pressed {{
    background: #0B1424;
    border-color: {COLORS["purple_soft"]};
}}

QPushButton:checked {{
    background: #182642;
    border: 1px solid {COLORS["purple_soft"]};
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
    background: #0B1626;
}}

QCheckBox::indicator:checked {{
    background: {COLORS["purple"]};
    border-color: {COLORS["purple_soft"]};
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
    background: #101B31;
    color: {COLORS["text"]};
    border-left: 3px solid {COLORS["purple_soft"]};
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
    background: #101B31;
    border-left: 3px solid {COLORS["purple_soft"]};
}}

QFrame#SidebarItemFrame:hover {{
    background: {COLORS["card"]};
}}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {{
    background: #0B1626;
    border: 1px solid {COLORS["border"]};
    border-radius: 11px;
    padding: 10px 13px;
    color: {COLORS["text"]};
    selection-background-color: {COLORS["blue"]};
}}

QFrame#SearchBox {{
    background: #0B1626;
    border: 1px solid {COLORS["border"]};
    border-radius: 11px;
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
    background: #0B1626;
    border: 1px solid {COLORS["border"]};
    border-radius: 11px;
    padding: 10px 38px 10px 13px;
    color: {COLORS["text"]};
    selection-background-color: {COLORS["purple"]};
    min-height: 20px;
}}

QComboBox:hover {{
    background: #0E1A2B;
    border-color: {COLORS["blue"]};
}}

QComboBox:focus {{
    border-color: {COLORS["purple_soft"]};
    background: #0E1A2B;
}}

QComboBox:disabled {{
    background: #08111D;
    border-color: #162235;
    color: #536176;
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 34px;
    border-left: 1px solid #1B2A42;
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
    background: #0E1A2B;
}}

QComboBox::drop-down:hover {{
    background: #121F33;
}}

QComboBox::down-arrow {{
    image: url(app/ui/assets/combo_down.svg);
    width: 12px;
    height: 12px;
}}

QComboBox QAbstractItemView {{
    background: #0B1626;
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    color: {COLORS["text"]};
    padding: 0;
    margin: 0;
    outline: 0;
    selection-background-color: #1D2F55;
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
    background: #12213A;
    color: {COLORS["text"]};
}}

QComboBox QAbstractItemView::item:selected {{
    background: #243A68;
    color: white;
}}

QSpinBox::up-button, QSpinBox::down-button {{
    background: #0E1A2B;
    border-left: 1px solid #1B2A42;
    width: 22px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: #121F33;
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
    background: rgba(59, 130, 246, 0.16);
    border-radius: 10px;
}}

QFrame#FileListItem {{
    background: #0B1626;
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
}}

QFrame#FileListItem:hover {{
    background: #101B31;
    border-color: {COLORS["blue"]};
}}

QFrame#Toast {{
    background: #0B1626;
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
}}

QFrame#StepCard {{
    background: #0B1626;
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

QProgressBar {{
    background: #162235;
    border: 0;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS["blue"]}, stop:1 {COLORS["purple_soft"]});
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
    border-bottom-color: {COLORS["blue"]};
}}
"""
