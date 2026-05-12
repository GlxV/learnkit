from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.services.block_service import BlockService
from app.core.services.module_service import ModuleService
from app.ui.feedback import confirm_action, log_action, show_toast
from app.ui.icon_catalog import MODULE_PRESETS, SUBJECT_ICONS
from app.ui.components.cards import EmptyState, ProgressLine, StatCard, StudyBlockRow, SubjectCard, label
from app.ui.components.visual import IconBadge
from app.ui.mock_data import UIDataProvider, UIModule, UISubject
from app.ui.pages.base import panel, scroll_page
from app.ui.theme import COLORS


class NewSubjectDialog(QDialog):
    COLORS = ["#3B82F6", "#7C3AED", "#16A34A", "#D97706", "#EC4899", "#06B6D4"]
    ICONS = SUBJECT_ICONS
    MODULES = MODULE_PRESETS

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("NewSubjectDialog")
        self.setWindowTitle("Nova materia personalizada")
        self.setModal(True)
        self.resize(720, 760)
        self.selected_color = self.COLORS[0]
        self.selected_icon = self.ICONS[0]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 24)
        layout.setSpacing(14)
        layout.addWidget(label("Nova materia personalizada", "Title"))
        layout.addWidget(label("Crie uma area local de estudo com cor, simbolo e modulos iniciais.", "Muted"))

        preview = panel()
        preview_layout = QHBoxLayout(preview)
        preview_layout.setContentsMargins(18, 16, 18, 16)
        preview_layout.setSpacing(14)
        self.preview_icon = IconBadge(self.selected_icon, self.selected_color, size=54, radius=14)
        preview_text = QVBoxLayout()
        self.preview_name = label("Nome da materia", "SectionTitle")
        self.preview_description = label("Descricao curta da materia.", "Muted")
        preview_text.addWidget(self.preview_name)
        preview_text.addWidget(self.preview_description)
        preview_layout.addWidget(self.preview_icon)
        preview_layout.addLayout(preview_text, 1)
        layout.addWidget(preview)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Ex: Banco de Dados")
        self.name.textChanged.connect(self._refresh_preview)
        self.description = QTextEdit()
        self.description.setFixedHeight(82)
        self.description.setPlaceholderText("Ex: SQL, modelo relacional e normalizacao.")
        self.description.textChanged.connect(self._refresh_preview)
        layout.addWidget(label("Nome da materia", "SmallTitle"))
        layout.addWidget(self.name)
        layout.addWidget(label("Descricao opcional", "SmallTitle"))
        layout.addWidget(self.description)

        layout.addWidget(label("Cor de destaque", "SmallTitle"))
        color_row = QHBoxLayout()
        self.color_buttons: list[QPushButton] = []
        for color in self.COLORS:
            button = QPushButton()
            button.setCheckable(True)
            button.setFixedSize(38, 38)
            button.setStyleSheet(
                f"QPushButton {{ background: {color}; border-radius: 19px; border: 2px solid transparent; }}"
                f"QPushButton:checked {{ border: 3px solid {COLORS['text']}; }}"
            )
            button.clicked.connect(lambda checked=False, value=color: self._set_color(value))
            self.color_buttons.append(button)
            color_row.addWidget(button)
        self.color_buttons[0].setChecked(True)
        color_row.addStretch()
        layout.addLayout(color_row)

        icon_header = QHBoxLayout()
        icon_header.addWidget(label("Simbolo", "SmallTitle"))
        icon_header.addStretch()
        icon_header.addWidget(label("100 opcoes prontas", "Weak"))
        layout.addLayout(icon_header)
        icon_scroll = QScrollArea()
        icon_scroll.setFixedHeight(168)
        icon_scroll.setWidgetResizable(True)
        icon_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        icon_container = QWidget()
        icon_grid = QGridLayout(icon_container)
        icon_grid.setContentsMargins(0, 0, 0, 0)
        icon_grid.setHorizontalSpacing(8)
        icon_grid.setVerticalSpacing(8)
        self.icon_group = QButtonGroup(self)
        self.icon_group.setExclusive(True)
        for index, icon in enumerate(self.ICONS):
            button = QPushButton(icon)
            button.setCheckable(True)
            button.setObjectName("GhostButton")
            button.setFixedHeight(38)
            button.clicked.connect(lambda checked=False, value=icon: self._set_icon(value))
            self.icon_group.addButton(button)
            icon_grid.addWidget(button, index // 6, index % 6)
            if index == 0:
                button.setChecked(True)
        icon_scroll.setWidget(icon_container)
        layout.addWidget(icon_scroll)

        module_header = QHBoxLayout()
        module_header.addWidget(label("Modulos iniciais", "SmallTitle"))
        module_header.addStretch()
        module_header.addWidget(label("Escolha presets ou escreva os seus", "Weak"))
        layout.addLayout(module_header)
        custom_row = QHBoxLayout()
        self.custom_module = QLineEdit()
        self.custom_module.setPlaceholderText("Ex: Prova 5, 4o Bimestre, Unidade 7")
        add_module = QPushButton("Adicionar modulo")
        add_module.clicked.connect(self._add_custom_module)
        self.custom_module.returnPressed.connect(self._add_custom_module)
        custom_row.addWidget(self.custom_module, 1)
        custom_row.addWidget(add_module)
        layout.addLayout(custom_row)

        module_scroll = QScrollArea()
        module_scroll.setFixedHeight(150)
        module_scroll.setWidgetResizable(True)
        module_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        module_container = QWidget()
        self.modules_grid = QGridLayout(module_container)
        self.modules_grid.setContentsMargins(0, 0, 0, 0)
        self.modules_grid.setHorizontalSpacing(16)
        self.modules_grid.setVerticalSpacing(8)
        self.module_checks: list[QCheckBox] = []
        for module in self.MODULES:
            self._add_module_check(module, checked=module in {"Geral", "Prova 1"})
        module_scroll.setWidget(module_container)
        layout.addWidget(module_scroll)

        actions = QHBoxLayout()
        actions.addStretch()
        cancel = QPushButton("Cancelar")
        create = QPushButton("Criar materia")
        create.setObjectName("PrimaryButton")
        cancel.clicked.connect(self.reject)
        create.clicked.connect(self.accept)
        actions.addWidget(cancel)
        actions.addWidget(create)
        layout.addLayout(actions)

    def selected_modules(self) -> list[str]:
        modules: list[str] = []
        seen: set[str] = set()
        for check in self.module_checks:
            value = check.text().strip()
            if check.isChecked() and value.casefold() not in seen:
                modules.append(value)
                seen.add(value.casefold())
        return modules

    def _add_module_check(self, module: str, checked: bool = True) -> None:
        if not module.strip():
            return
        if any(check.text().casefold() == module.strip().casefold() for check in self.module_checks):
            return
        check = QCheckBox(module.strip())
        check.setChecked(checked)
        self.module_checks.append(check)
        index = len(self.module_checks) - 1
        self.modules_grid.addWidget(check, index // 3, index % 3)

    def _add_custom_module(self) -> None:
        module = self.custom_module.text().strip()
        if not module:
            return
        self._add_module_check(module, checked=True)
        self.custom_module.clear()

    def _set_color(self, color: str) -> None:
        self.selected_color = color
        for button, item_color in zip(self.color_buttons, self.COLORS):
            button.setChecked(item_color == color)
        self._refresh_preview()

    def _set_icon(self, icon: str) -> None:
        self.selected_icon = icon
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        name = self.name.text().strip() or "Nome da materia"
        description = self.description.toPlainText().strip() or "Descricao curta da materia."
        self.preview_name.setText(name)
        self.preview_description.setText(description)
        self.preview_icon.setText(self.selected_icon)
        self.preview_icon.setStyleSheet(
            f"background: {self.selected_color}; border-radius: 14px; color: white; "
            "font-size: 17px; font-weight: 850;"
        )


class NewModuleDialog(QDialog):
    def __init__(self, subject_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Criar modulo")
        self.resize(460, 300)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)
        layout.addWidget(label("Criar modulo", "Title"))
        layout.addWidget(label(f"Materia: {subject_name}", "Muted"))
        self.name = QLineEdit()
        self.name.setPlaceholderText("Ex: Prova 2, Recuperacao, Unidade 4")
        self.description = QTextEdit()
        self.description.setFixedHeight(80)
        self.description.setPlaceholderText("Descricao opcional do modulo")
        layout.addWidget(label("Nome do modulo", "SmallTitle"))
        layout.addWidget(self.name)
        layout.addWidget(label("Descricao", "SmallTitle"))
        layout.addWidget(self.description)
        actions = QHBoxLayout()
        actions.addStretch()
        cancel = QPushButton("Cancelar")
        create = QPushButton("Criar modulo")
        create.setObjectName("PrimaryButton")
        cancel.clicked.connect(self.reject)
        create.clicked.connect(self.accept)
        actions.addWidget(cancel)
        actions.addWidget(create)
        layout.addLayout(actions)


class SubjectsPage(QWidget):
    def __init__(self, provider: UIDataProvider) -> None:
        super().__init__()
        self.provider = provider
        self.subjects = provider.subjects()
        self.selected_subject: UISubject | None = self.subjects[0] if self.subjects else None
        self.selected_module: UIModule | None = (
            self.selected_subject.modules[0] if self.selected_subject and self.selected_subject.modules else None
        )
        self.root = QHBoxLayout(self)
        self.root.setContentsMargins(24, 24, 24, 24)
        self.root.setSpacing(18)
        self._build()

    def refresh(self) -> None:
        current_subject = self.selected_subject.name if self.selected_subject else ""
        current_module = self.selected_module.name if self.selected_module else ""
        self.subjects = self.provider.subjects()
        self.selected_subject = next(
            (subject for subject in self.subjects if subject.name == current_subject),
            self.subjects[0] if self.subjects else None,
        )
        self.selected_module = None
        if self.selected_subject:
            self.selected_module = next(
                (module for module in self.selected_subject.modules if module.name == current_module),
                self.selected_subject.modules[0] if self.selected_subject.modules else None,
            )
        self._rebuild()

    def select_subject_by_name(self, subject_name: str, module_name: str | None = None) -> None:
        self.subjects = self.provider.subjects()
        self.selected_subject = next((subject for subject in self.subjects if subject.name == subject_name), None)
        if self.selected_subject:
            self.selected_module = next(
                (module for module in self.selected_subject.modules if module.name == module_name),
                self.selected_subject.modules[0] if self.selected_subject.modules else None,
            )
            self._rebuild()

    def _build(self) -> None:
        left = panel()
        left.setFixedWidth(330)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(12)
        left_layout.addWidget(label("Explorar materias", "SectionTitle"))
        for subject in self.subjects:
            card = SubjectCard(subject)
            card.clicked.connect(self._select_subject)
            left_layout.addWidget(card)
        add = QPushButton("Nova materia personalizada")
        add.setObjectName("PrimaryButton")
        add.clicked.connect(self._new_subject)
        left_layout.addWidget(add)
        left_layout.addStretch()
        self.root.addWidget(left)

        scroll, _, self.detail_layout = scroll_page()
        self.root.addWidget(scroll, 1)
        self._render_detail()

    def _render_detail(self) -> None:
        self._clear_layout(self.detail_layout)
        if not self.selected_subject:
            empty = EmptyState(
                "Nenhuma materia criada ainda.",
                "Crie uma materia personalizada para organizar modulos e blocos reais.",
            )
            layout = empty.layout()
            if layout is not None:
                button = QPushButton("Criar materia")
                button.setObjectName("PrimaryButton")
                button.clicked.connect(self._new_subject)
                layout.addWidget(button)
            self.detail_layout.addWidget(empty)
            self.detail_layout.addStretch()
            return

        subject = self.selected_subject
        modules = subject.modules
        blocks = [block for module in modules for block in module.blocks]

        hero = panel()
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(22, 20, 22, 20)
        hero_layout.setSpacing(18)
        hero_layout.addWidget(IconBadge(subject.icon, subject.color, size=70, radius=18, font_size=20))
        text_box = QVBoxLayout()
        text_box.addWidget(label(subject.name, "Title"))
        text_box.addWidget(label(subject.description, "Muted"))
        progress_row = QHBoxLayout()
        progress_row.addWidget(ProgressLine(subject.progress), 1)
        progress_row.addWidget(label(f"{subject.progress}% concluido", "Muted"))
        text_box.addLayout(progress_row)
        hero_layout.addLayout(text_box, 1)

        actions = QVBoxLayout()
        study_subject = QPushButton("Estudar materia")
        study_subject.clicked.connect(lambda: self._navigate("studies"))
        create_module = QPushButton("Criar modulo")
        create_module.clicked.connect(self._new_module)
        add_block = QPushButton("Adicionar bloco")
        add_block.setObjectName("PrimaryButton")
        add_block.clicked.connect(lambda: self._navigate("import"))
        delete_subject = QPushButton("Excluir materia")
        delete_subject.setObjectName("GhostButton")
        delete_subject.clicked.connect(self._delete_subject)
        actions.addWidget(study_subject)
        actions.addWidget(add_block)
        actions.addWidget(create_module)
        actions.addWidget(delete_subject)
        hero_layout.addLayout(actions)
        self.detail_layout.addWidget(hero)

        stats = QHBoxLayout()
        stats.addWidget(StatCard("Modulos", str(len(modules)), "organizados", "studies"))
        stats.addWidget(StatCard("Blocos", str(len(blocks)), "pacotes de estudo", "blocks"))
        stats.addWidget(StatCard("Flashcards", str(sum(block.flashcards for block in blocks)), "para revisar", "flashcards"))
        stats.addWidget(StatCard("Perguntas", str(sum(block.questions for block in blocks)), "multipla escolha", "questions"))
        self.detail_layout.addLayout(stats)

        header = QHBoxLayout()
        header.addWidget(label("Modulos", "SectionTitle"))
        header.addStretch()
        self.detail_layout.addLayout(header)

        if not modules:
            empty = EmptyState("Nenhum modulo nesta materia.", "Crie um modulo antes de adicionar blocos.")
            empty_layout = empty.layout()
            if empty_layout is not None:
                button = QPushButton("Criar modulo")
                button.setObjectName("PrimaryButton")
                button.clicked.connect(self._new_module)
                empty_layout.addWidget(button)
            self.detail_layout.addWidget(empty)
            self.detail_layout.addStretch()
            return

        module_grid = QGridLayout()
        module_grid.setHorizontalSpacing(12)
        module_grid.setVerticalSpacing(12)
        for index, module in enumerate(modules):
            module_grid.addWidget(self._module_card(module), index // 2, index % 2)
        self.detail_layout.addLayout(module_grid)

        self._render_blocks_panel()
        self.detail_layout.addStretch()

    def _module_card(self, module: UIModule) -> QWidget:
        card = panel()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        header = QHBoxLayout()
        header.addWidget(IconBadge("M", self.selected_subject.color if self.selected_subject else COLORS["purple"], size=38, radius=10))
        title_box = QVBoxLayout()
        title_box.addWidget(label(module.name, "SmallTitle"))
        title_box.addWidget(label(f"{len(module.blocks)} blocos", "Weak"))
        header.addLayout(title_box, 1)
        header.addWidget(label(f"{module.progress}%", "Muted"))
        layout.addLayout(header)
        layout.addWidget(ProgressLine(module.progress))
        actions = QHBoxLayout()
        open_button = QPushButton("Abrir")
        open_button.setObjectName("GhostButton")
        open_button.clicked.connect(lambda checked=False, name=module.name: self._select_module(name))
        delete_button = QPushButton("Excluir")
        delete_button.setObjectName("GhostButton")
        delete_button.clicked.connect(lambda checked=False, item=module: self._delete_module(item))
        actions.addWidget(open_button)
        actions.addWidget(delete_button)
        layout.addLayout(actions)
        return card

    def _render_blocks_panel(self) -> None:
        module_name = self.selected_module.name if self.selected_module else "sem modulo"
        block_panel = panel()
        block_layout = QVBoxLayout(block_panel)
        block_layout.setContentsMargins(18, 16, 18, 16)
        block_layout.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(label(f"Blocos do modulo: {module_name}", "SectionTitle"))
        header.addStretch()
        add_block = QPushButton("Adicionar bloco")
        add_block.setObjectName("PrimaryButton")
        add_block.clicked.connect(lambda: self._navigate("import"))
        header.addWidget(add_block)
        block_layout.addLayout(header)
        if self.selected_module and self.selected_module.blocks:
            for block in self.selected_module.blocks:
                row = StudyBlockRow(block)
                row.open_requested.connect(lambda block_id: self._open_block(block_id, "studies"))
                delete_button = QPushButton("Excluir bloco")
                delete_button.setObjectName("GhostButton")
                delete_button.clicked.connect(lambda checked=False, item=block: self._delete_block(item.title))
                wrapper = QHBoxLayout()
                wrapper.addWidget(row, 1)
                wrapper.addWidget(delete_button)
                block_layout.addLayout(wrapper)
        else:
            block_layout.addWidget(
                EmptyState("Nenhum bloco neste modulo.", "Use Importacao/IA para criar um pacote de estudo completo.")
            )
        self.detail_layout.addWidget(block_panel)

    def _select_subject(self, name: str) -> None:
        self.selected_subject = next(subject for subject in self.subjects if subject.name == name)
        self.selected_module = self.selected_subject.modules[0] if self.selected_subject.modules else None
        self._render_detail()

    def _select_module(self, name: str) -> None:
        if not self.selected_subject:
            return
        self.selected_module = next(module for module in self.selected_subject.modules if module.name == name)
        self._render_detail()

    def _new_subject(self) -> None:
        dialog = NewSubjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.name.text().strip():
            name = dialog.name.text().strip()
            self.provider.create_subject(
                name,
                dialog.description.toPlainText().strip(),
                color=dialog.selected_color,
                icon=dialog.selected_icon,
                initial_modules=dialog.selected_modules(),
            )
            self.subjects = self.provider.subjects()
            self.selected_subject = next((subject for subject in self.subjects if subject.name == name), self.subjects[0])
            self.selected_module = self.selected_subject.modules[0] if self.selected_subject.modules else None
            show_toast(self, f"Materia criada: {name}", "success")
            log_action("subject_created", subject=name)
            self._rebuild()

    def _new_module(self) -> None:
        if not self.selected_subject:
            QMessageBox.information(self, "Crie uma materia", "Crie uma materia antes de adicionar modulos.")
            return
        dialog = NewModuleDialog(self.selected_subject.name, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.name.text().strip():
            self.provider.create_module(
                self.selected_subject.name,
                dialog.name.text().strip(),
                dialog.description.toPlainText().strip(),
            )
            show_toast(self, f"Modulo criado: {dialog.name.text().strip()}", "success")
            log_action("module_created", subject=self.selected_subject.name, module=dialog.name.text().strip())
            self.refresh()

    def _delete_subject(self) -> None:
        if not self.selected_subject:
            return
        if confirm_action(self, "Excluir materia", f"Excluir '{self.selected_subject.name}' e todos os modulos/blocos locais?"):
            name = self.selected_subject.name
            self.provider.storage.delete_subject(self.selected_subject.name)
            show_toast(self, f"Materia excluida: {name}", "success")
            log_action("subject_deleted", subject=name)
            self.refresh()

    def _delete_module(self, module: UIModule) -> None:
        if not self.selected_subject:
            return
        if confirm_action(self, "Excluir modulo", f"Excluir o modulo '{module.name}'?"):
            ModuleService(self.provider.storage).delete_module(self.selected_subject.name, module.name)
            show_toast(self, f"Modulo excluido: {module.name}", "success")
            log_action("module_deleted", subject=self.selected_subject.name, module=module.name)
            self.refresh()

    def _delete_block(self, block_title: str) -> None:
        if not self.selected_subject or not self.selected_module:
            return
        if confirm_action(self, "Excluir bloco", f"Excluir o bloco '{block_title}'?"):
            BlockService(self.provider.storage).delete_block(
                self.selected_subject.name,
                self.selected_module.name,
                block_title,
            )
            show_toast(self, f"Bloco excluido: {block_title}", "success")
            log_action("block_deleted", subject=self.selected_subject.name, module=self.selected_module.name, block=block_title)
            self.refresh()

    def _open_block(self, block_id: str, destination: str) -> None:
        window = self.window()
        if hasattr(window, "open_block"):
            window.open_block(block_id, destination)
        else:
            self._navigate(destination)

    def _navigate(self, key: str) -> None:
        window = self.window()
        if hasattr(window, "navigate"):
            window.navigate(key)

    def _rebuild(self) -> None:
        while self.root.count():
            item = self.root.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._build()

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
