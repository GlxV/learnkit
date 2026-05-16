import os
import sys


def test_main_window_instantiates_offscreen() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from app.ui.main_window import MainWindow
    from app.ui.theme import apply_app_theme

    app = QApplication.instance() or QApplication(sys.argv)
    apply_app_theme(app)
    window = MainWindow()

    assert window.windowTitle() == "LearnKit"
    assert window.stack.count() == 9


def test_new_subject_dialog_has_scrollable_hex_icon_controls() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QScrollArea

    from app.ui.pages.subjects_page import NewSubjectDialog
    from app.ui.theme import apply_app_theme

    app = QApplication.instance() or QApplication(sys.argv)
    apply_app_theme(app)
    dialog = NewSubjectDialog()

    dialog.hex_color.setText("#FFAA00")

    assert dialog.findChild(QScrollArea) is not None
    assert dialog._apply_hex_color_from_input() is True
    assert dialog.selected_color == "#FFAA00"
    assert dialog.selected_icon == "calculator"
    assert dialog.icon_buttons
    assert dialog.icon_buttons[0].text() == ""


def test_edit_subject_dialog_prefills_without_initial_modules() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from app.application.query_services.ui_data_provider import UISubject
    from app.ui.pages.subjects_page import NewSubjectDialog
    from app.ui.theme import apply_app_theme

    app = QApplication.instance() or QApplication(sys.argv)
    apply_app_theme(app)
    subject = UISubject(
        "Banco de Dados",
        "Modelo relacional",
        0,
        "#14B8A6",
        "database",
        [],
        id="subject-1",
    )
    dialog = NewSubjectDialog(subject=subject)

    assert dialog.is_editing is True
    assert dialog.name.text() == "Banco de Dados"
    assert dialog.description.toPlainText() == "Modelo relacional"
    assert dialog.selected_color == "#14B8A6"
    assert dialog.selected_icon == "database"
    assert dialog.selected_modules() == []


def test_subject_catalog_use_case_updates_subject_metadata(tmp_path) -> None:
    from app.application.use_cases.manage_subject_catalog import ManageSubjectCatalogUseCase
    from app.core.database.sqlite_storage import SQLiteStorage

    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    use_case = ManageSubjectCatalogUseCase(storage)
    use_case.create_subject("Matematica", "Descricao antiga", color="#3B82F6", icon="calculator")

    subject = storage.get_subject("Matematica")
    use_case.update_subject(
        subject.id,
        "Matematica Aplicada",
        "Descricao nova",
        color="#EC4899",
        icon="chart",
    )
    updated = storage.get_subject("Matematica Aplicada")

    assert updated.id == subject.id
    assert updated.description == "Descricao nova"
    assert updated.color == "#EC4899"
    assert updated.icon == "chart"
