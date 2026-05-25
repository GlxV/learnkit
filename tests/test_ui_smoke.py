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
    assert window.stack.count() == 10


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


def test_visual_summary_widget_renders_rich_blocks_offscreen() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QScrollArea

    from app.ui.components.summary_visual import PresentationDialog, VisualSummaryWidget
    from app.ui.theme import apply_app_theme

    app = QApplication.instance() or QApplication(sys.argv)
    apply_app_theme(app)
    raw = """
    {
      "title": "Estruturas de Dados",
      "subtitle": "Revisao visual",
      "sections": [
        {"type": "hero", "title": "Ideia central", "text": "Organizar acesso e custo."},
        {"type": "cards", "items": [{"title": "Array", "text": "Indice direto."}]},
        {"type": "callout", "variant": "warning", "title": "Pegadinha", "text": "Custo muda."},
        {"type": "table", "headers": ["Tipo", "Uso"], "rows": [["Pilha", "LIFO"]]},
        {"type": "chart", "chart_type": "bar", "labels": ["Array"], "values": [90]}
      ]
    }
    """

    widget = VisualSummaryWidget(raw)
    dialog = PresentationDialog("Estruturas de Dados", raw)

    assert widget.findChildren(QScrollArea)
    assert dialog.counter.text() == "1 / 5"


def test_visual_summary_widget_renders_non_standard_item_fields() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QLabel

    from app.ui.components.summary_visual import VisualSummaryWidget
    from app.ui.theme import apply_app_theme

    app = QApplication.instance() or QApplication(sys.argv)
    apply_app_theme(app)
    raw = """
    {
      "title": "Estruturas",
      "sections": [
        {
          "type": "mistakes",
          "title": "Erros comuns",
          "items": [
            {
              "mistake": "Confundir fila com pilha.",
              "correction": "Fila segue FIFO; pilha segue LIFO."
            }
          ]
        },
        {
          "type": "steps",
          "title": "Insercao",
          "items": [
            {"step": 1, "title": "Inserir 15", "text": "O valor vira raiz."}
          ]
        },
        {
          "type": "flow",
          "title": "Fluxo",
          "nodes": [
            {"id": "head", "label": "Cabeca"},
            {"id": "node1", "label": "No: dado + proximo"}
          ],
          "edges": [{"from": "head", "to": "node1"}]
        }
      ]
    }
    """

    widget = VisualSummaryWidget(raw)
    texts = [child.text() for child in widget.findChildren(QLabel)]

    assert "Confundir fila com pilha." in texts
    assert "Fila segue FIFO; pilha segue LIFO." in texts
    assert "Inserir 15" in texts
    assert "O valor vira raiz." in texts
    assert "Cabeca" in texts
    assert "No: dado + proximo" in texts
    assert "Item" not in texts
