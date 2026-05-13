from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.services.backup_service import BackupService
from app.core.storage.local_storage import LocalStorage
from app.ui.components.cards import label
from app.ui.feedback import confirm_action, log_action, show_toast
from app.ui.pages.base import panel, scroll_page
from app.ui.theme import THEME_PRESETS, apply_app_theme_settings


class SettingsPage(QWidget):
    def __init__(self, storage: LocalStorage | None = None) -> None:
        super().__init__()
        self.storage = storage or LocalStorage("data")
        self.settings_path = self.storage.base_path / "settings.json"
        self.settings = self._load_settings()
        self.custom_fields: dict[str, QLineEdit] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll, _, self.layout = scroll_page()
        root.addWidget(scroll)
        self._build()

    def _build(self) -> None:
        self.layout.addWidget(label("Configurações", "Title"))
        self.layout.addWidget(label("Preferências locais, temas e armazenamento. Sem API paga ou cloud.", "Muted"))

        self._build_appearance()
        self._build_study_settings()
        self._build_storage_settings()
        self._build_shortcuts()

        actions = QHBoxLayout()
        actions.addStretch()
        apply_theme = QPushButton("Aplicar tema")
        apply_theme.clicked.connect(self._apply_theme_preview)
        save = QPushButton("Salvar configuracoes")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(self._save_settings)
        actions.addWidget(apply_theme)
        actions.addWidget(save)
        self.layout.addLayout(actions)
        self.layout.addStretch()
        self._apply_loaded_values()

    def _build_appearance(self) -> None:
        appearance = panel()
        form = QFormLayout(appearance)
        form.setContentsMargins(18, 16, 18, 16)
        form.addRow(label("Aparência", "SectionTitle"))

        self.theme_preset = QComboBox()
        self.theme_preset.addItems(list(THEME_PRESETS.keys()))
        self.theme_preset.currentTextChanged.connect(self._load_preset_into_fields)
        self.density = QComboBox()
        self.density.addItems(["Confortável", "Compacta", "Densa"])
        self.animations = QCheckBox()

        form.addRow("Preset de tema", self.theme_preset)
        form.addRow("Densidade", self.density)
        form.addRow("Animacoes sutis", self.animations)

        for key, title in [
            ("background", "Fundo"),
            ("background_alt", "Fundo secundário"),
            ("surface", "Barras/superfícies"),
            ("card", "Cards"),
            ("card_alt", "Cards destacados"),
            ("border", "Bordas"),
            ("text", "Texto principal"),
            ("muted", "Texto secundario"),
            ("accent", "Destaque principal"),
            ("secondary", "Destaque secundario"),
        ]:
            field = QLineEdit()
            field.setPlaceholderText("#0B1626")
            field.textChanged.connect(self._update_theme_preview)
            self.custom_fields[key] = field
            form.addRow(title, field)

        self.theme_preview = label("Preview do tema", "Muted")
        self.theme_preview.setMinimumHeight(56)
        form.addRow("Preview", self.theme_preview)
        self.layout.addWidget(appearance)

    def _build_study_settings(self) -> None:
        studies = panel()
        study_form = QFormLayout(studies)
        study_form.setContentsMargins(18, 16, 18, 16)
        study_form.addRow(label("Estudos", "SectionTitle"))
        self.resume = QCheckBox()
        self.auto_review = QCheckBox()
        self.question_order = QComboBox()
        self.question_order.addItems(["Ordem original", "Aleatória", "Mais erradas primeiro"])
        self.show_explanations = QCheckBox()
        self.confirm_exit = QCheckBox()
        study_form.addRow("Iniciar onde parou", self.resume)
        study_form.addRow("Revisão automática", self.auto_review)
        study_form.addRow("Ordem das questões", self.question_order)
        study_form.addRow("Mostrar explicações primeiro", self.show_explanations)
        study_form.addRow("Confirmar saída de simulado", self.confirm_exit)
        self.layout.addWidget(studies)

    def _build_storage_settings(self) -> None:
        storage = panel()
        storage_form = QFormLayout(storage)
        storage_form.setContentsMargins(18, 16, 18, 16)
        storage_form.addRow(label("Arquivos e armazenamento local", "SectionTitle"))
        self.data_path = QLineEdit(str(self.storage.base_path))
        self.backup_auto = QCheckBox()

        browse_folder = QPushButton("Escolher pasta")
        browse_folder.clicked.connect(self._choose_data_folder)
        open_folder = QPushButton("Abrir pasta de dados")
        open_folder.clicked.connect(self._open_data_folder)
        export_data = QPushButton("Exportar dados")
        export_data.clicked.connect(self._export_data)
        import_data = QPushButton("Importar backup")
        import_data.clicked.connect(self._import_data)
        clear_cache = QPushButton("Limpar cache")
        clear_cache.clicked.connect(self._clear_cache)
        backup_now = QPushButton("Criar backup agora")
        backup_now.setObjectName("PrimaryButton")
        backup_now.clicked.connect(self._backup_now)

        path_row = QHBoxLayout()
        path_row.addWidget(self.data_path, 1)
        path_row.addWidget(browse_folder)
        storage_form.addRow("Pasta de dados", path_row)
        storage_form.addRow("Abrir local", open_folder)
        storage_form.addRow("Exportar", export_data)
        storage_form.addRow("Importar", import_data)
        storage_form.addRow("Cache", clear_cache)
        storage_form.addRow("Backup automático", self.backup_auto)
        storage_form.addRow("Backup manual", backup_now)
        self.layout.addWidget(storage)

    def _build_shortcuts(self) -> None:
        shortcuts = panel()
        form = QFormLayout(shortcuts)
        form.setContentsMargins(18, 16, 18, 16)
        form.addRow(label("Atalhos de teclado", "SectionTitle"))
        self.shortcut_fields: dict[str, QLineEdit] = {}
        defaults = {
            "Buscar": "Ctrl+K",
            "Estudar agora": "Ctrl+Enter",
            "Próxima questão": "Right",
            "Questão anterior": "Left",
            "Virar flashcard": "Space",
            "Tela cheia": "F11",
        }
        for name, value in defaults.items():
            field = QLineEdit(value)
            self.shortcut_fields[name] = field
            form.addRow(name, field)
        self.layout.addWidget(shortcuts)

    def _apply_loaded_values(self) -> None:
        self._set_combo(self.theme_preset, str(self.settings.get("theme_preset", "LearnKit Dark")))
        self._set_combo(self.density, str(self.settings.get("density", "Confortável")))
        self._set_combo(self.question_order, str(self.settings.get("question_order", "Ordem original")))
        self.animations.setChecked(bool(self.settings.get("animations", True)))
        self.resume.setChecked(bool(self.settings.get("resume_last_block", True)))
        self.auto_review.setChecked(bool(self.settings.get("auto_review", False)))
        self.show_explanations.setChecked(bool(self.settings.get("show_explanations_first", False)))
        self.confirm_exit.setChecked(bool(self.settings.get("confirm_exit_exam", True)))
        self.backup_auto.setChecked(bool(self.settings.get("backup_auto", False)))
        self.data_path.setText(str(self.settings.get("data_path", self.storage.base_path)))

        custom = self.settings.get("custom_theme")
        if isinstance(custom, dict):
            for key, field in self.custom_fields.items():
                field.setText(str(custom.get(key, "")))
        else:
            self._load_preset_into_fields(self.theme_preset.currentText())

        shortcuts = self.settings.get("shortcuts")
        if isinstance(shortcuts, dict):
            for name, field in self.shortcut_fields.items():
                if name in shortcuts:
                    field.setText(str(shortcuts[name]))
        self._update_theme_preview()

    def _load_preset_into_fields(self, preset_name: str) -> None:
        preset = THEME_PRESETS.get(preset_name)
        if not preset:
            return
        for key, field in self.custom_fields.items():
            field.setText(preset.get(key, ""))
        self._update_theme_preview()

    def _collect_settings(self) -> dict[str, object]:
        return {
            "theme_preset": self.theme_preset.currentText(),
            "custom_theme": {key: field.text().strip() for key, field in self.custom_fields.items()},
            "density": self.density.currentText(),
            "animations": self.animations.isChecked(),
            "resume_last_block": self.resume.isChecked(),
            "auto_review": self.auto_review.isChecked(),
            "question_order": self.question_order.currentText(),
            "show_explanations_first": self.show_explanations.isChecked(),
            "confirm_exit_exam": self.confirm_exit.isChecked(),
            "data_path": self.data_path.text().strip() or str(self.storage.base_path),
            "backup_auto": self.backup_auto.isChecked(),
            "shortcuts": {name: field.text().strip() for name, field in self.shortcut_fields.items()},
        }

    def _save_settings(self) -> None:
        self.settings = self._collect_settings()
        target_data_path = Path(str(self.settings["data_path"]))
        target_data_path.mkdir(parents=True, exist_ok=True)
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps(self.settings, ensure_ascii=False, indent=2), encoding="utf-8")
        self._apply_theme_preview()
        show_toast(self, "Configurações salvas.", "success")
        log_action("settings_saved", path=self.settings_path)

    def _apply_theme_preview(self) -> None:
        settings = self._collect_settings()
        app = QApplication.instance()
        if app is not None:
            apply_app_theme_settings(app, settings)
        self._update_theme_preview()
        show_toast(self, "Tema aplicado.", "success")

    def _update_theme_preview(self) -> None:
        accent = self.custom_fields.get("accent")
        card = self.custom_fields.get("card")
        text = self.custom_fields.get("text")
        muted = self.custom_fields.get("muted")
        accent_value = accent.text().strip() if accent else "#3B82F6"
        card_value = card.text().strip() if card else "#0B1626"
        text_value = text.text().strip() if text else "#F3F6FB"
        muted_value = muted.text().strip() if muted else "#9BA8BA"
        self.theme_preview.setText("Cards, bordas, texto e destaque usam estes valores ao aplicar.")
        self.theme_preview.setStyleSheet(
            f"background: {card_value}; color: {text_value}; border: 1px solid {accent_value}; "
            f"border-radius: 12px; padding: 14px; selection-color: {muted_value};"
        )

    def _choose_data_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Escolher pasta de dados", self.data_path.text())
        if selected:
            self.data_path.setText(selected)
            show_toast(self, "Pasta selecionada. Salve para persistir.", "info")

    def _open_data_folder(self) -> None:
        path = Path(self.data_path.text().strip() or self.storage.base_path)
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path.resolve())  # type: ignore[attr-defined]
        show_toast(self, "Pasta de dados aberta.", "info")
        log_action("data_folder_opened", path=path)

    def _export_data(self) -> None:
        output = QFileDialog.getExistingDirectory(self, "Escolher pasta para exportar backup", "backups")
        if not output:
            return
        path = BackupService(self.storage).export_all_data(output)
        show_toast(self, f"Backup exportado: {path}", "success")
        log_action("data_exported", path=path)

    def _import_data(self) -> None:
        archive_path, _ = QFileDialog.getOpenFileName(self, "Importar backup", "", "Backup LearnKit (*.zip)")
        if not archive_path:
            return
        if not confirm_action(
            self,
            "Importar backup",
            "Importar este backup vai mesclar arquivos no diretório de dados atual. Continuar?",
        ):
            return
        imported = 0
        with ZipFile(archive_path) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                target = (self.storage.base_path / member.filename).resolve()
                base = self.storage.base_path.resolve()
                if base not in target.parents and target != base:
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(member))
                imported += 1
        show_toast(self, f"Backup importado ({imported} arquivos).", "success")
        log_action("data_imported", path=archive_path, files=imported)

    def _backup_now(self) -> None:
        path = BackupService(self.storage).export_all_data("backups")
        show_toast(self, f"Backup criado: {path}", "success")
        log_action("backup_created", path=path)

    def _clear_cache(self) -> None:
        if not confirm_action(self, "Limpar cache", "Remover caches Python locais (__pycache__ e .pytest_cache)?"):
            return
        removed = 0
        for path in [Path(".pytest_cache"), *Path("app").rglob("__pycache__"), *Path("tests").rglob("__pycache__")]:
            if path.exists():
                shutil.rmtree(path)
                removed += 1
        show_toast(self, f"Cache limpo ({removed} pasta(s)).", "success")
        log_action("cache_cleared", removed=removed)

    def _load_settings(self) -> dict[str, object]:
        if not self.settings_path.exists():
            return {}
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _set_combo(self, combo: QComboBox, value: str) -> None:
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)
