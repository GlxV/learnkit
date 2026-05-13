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
