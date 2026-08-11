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
    assert dialog.progress.value() == 20
    assert dialog.fullscreen_button.isCheckable()
    assert not dialog.previous_button.isEnabled()
    assert dialog.next_button.isEnabled()


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


def test_visual_summary_widget_renders_new_premium_block_types() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QLabel

    from app.ui.components.summary_visual import VisualSummaryWidget
    from app.ui.theme import apply_app_theme

    app = QApplication.instance() or QApplication(sys.argv)
    apply_app_theme(app)
    raw = """
    {
      "title": "Micologia",
      "style": "lab",
      "sections": [
        {"type": "mindmap", "title": "Mapa mental", "items": [{"title": "Hifas", "text": "Filamentos"}]},
        {"type": "concept_map", "title": "Mapa de conceitos", "items": [{"title": "Micelio", "text": "Rede"}]},
        {"type": "exam_trap", "title": "Pegadinha", "text": "Levedura nao e sempre filamentosa."},
        {"type": "source_quote", "quote": "Fungos absorvem nutrientes.", "source": "Apostila"},
        {"type": "quiz_preview", "items": [{"title": "Como cai?", "text": "Comparar grupos."}]}
      ]
    }
    """

    widget = VisualSummaryWidget(raw)
    texts = [child.text() for child in widget.findChildren(QLabel)]

    assert "Mapa mental" in texts
    assert "Hifas" in texts
    assert "Pegadinha" in texts
    assert '"Fungos absorvem nutrientes."' in texts
    assert "Como cai?" in texts


def test_import_page_guided_flow_defaults_and_modes(tmp_path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from app.core.database.sqlite_storage import SQLiteStorage
    from app.ui.pages.import_page import ImportPage
    from app.ui.theme import apply_app_theme

    app = QApplication.instance() or QApplication(sys.argv)
    apply_app_theme(app)
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Biologia")
    module = storage.create_module(subject.slug, "Micologia")
    storage.create_block(subject.slug, module.slug, "Fungos")

    page = ImportPage([], storage)
    page.subject_combo.setCurrentText("Biologia")
    page.module_combo.setCurrentText("Micologia")
    page.refresh()

    assert page.wizard_stack.currentIndex() == 0
    assert page.create_action_button.isChecked()
    assert not page.update_action_button.isChecked()
    assert page.options_panel.isHidden()
    assert page.advanced_import_panel.isHidden()
    assert page.flashcard_count.value() == 10
    assert page.question_count.value() == 10
    assert page.language_combo.currentText() == "direta para prova"
    assert page.summary_mode_combo.currentText() == "texto + visual avancado"
    assert page.visual_style_combo.currentData() == "auto"

    page.update_action_button.click()

    assert page._is_update_mode() is True
    assert page.existing_block_combo.currentData() is not None
    assert page.block_title.isEnabled() is False


def test_import_page_validation_card_updates_from_json_response(tmp_path, monkeypatch) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QLabel

    from app.core.database.sqlite_storage import SQLiteStorage
    import app.ui.pages.import_page as import_page_module
    from app.ui.pages.import_page import ImportPage
    from app.ui.theme import apply_app_theme

    app = QApplication.instance() or QApplication(sys.argv)
    apply_app_theme(app)
    monkeypatch.setattr(import_page_module, "show_toast", lambda *args, **kwargs: None)
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    page = ImportPage([], storage)
    page.ai_response.setPlainText(
        """
        {
          "schema_version": "learnkit.study_package.v1",
          "summary_text": "Resumo curto.",
          "summary_visual": {"title": "Teste", "style": "neon", "sections": [{"type": "hero", "title": "Centro"}]},
          "flashcards": [{"front": "Pergunta?", "back": "Resposta."}],
          "questions": [
            {
              "statement": "Enunciado?",
              "alternatives": {"A": "A", "B": "B", "C": "C", "D": "D"},
              "correct_answer": "A"
            }
          ]
        }
        """
    )

    page._validate_response()
    metric_values = [label.text() for label in page.validation_card.findChildren(QLabel)]

    assert page.parsed_response is not None
    assert page.save_button.isEnabled()
    assert "sim" in metric_values
    assert "1" in metric_values
    assert "Pacote validado" in page.response_status.text()


def test_import_page_validation_separates_warnings_and_filters_invalid_items(tmp_path, monkeypatch) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QLabel

    from app.core.database.sqlite_storage import SQLiteStorage
    import app.ui.pages.import_page as import_page_module
    from app.ui.pages.import_page import ImportPage
    from app.ui.theme import apply_app_theme

    app = QApplication.instance() or QApplication(sys.argv)
    apply_app_theme(app)
    monkeypatch.setattr(import_page_module, "show_toast", lambda *args, **kwargs: None)
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    page = ImportPage([], storage)
    page.ai_response.setPlainText(
        '{"summary_text":"Resumo", "flashcards":[{"front":"F","back":"R"}],'
        '"questions":[{"statement":"Valida?","alternatives":{"A":"A","B":"B","C":"C","D":"D"},"correct_answer":"A"},'
        '{"statement":"Incompleta?","alternatives":{"A":"A"},"correct_answer":"A"}]}'
    )

    page._validate_response()
    metric_values = [label.text() for label in page.validation_card.findChildren(QLabel)]

    assert page.validation_report is not None
    assert len(page.validation_report.warning_issues) == 1
    assert page.parsed_response is not None
    assert len(page.parsed_response.questions) == 1
    assert page.save_button.isEnabled()
    assert "1/2" in metric_values
    assert page.validation_details_button.isEnabled()


def test_import_page_prepare_button_orchestrates_existing_steps(tmp_path, monkeypatch) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from types import SimpleNamespace
    from PySide6.QtWidgets import QApplication

    from app.core.database.sqlite_storage import SQLiteStorage
    import app.ui.pages.import_page as import_page_module
    from app.ui.pages.import_page import ImportPage
    from app.ui.theme import apply_app_theme

    app = QApplication.instance() or QApplication(sys.argv)
    apply_app_theme(app)
    monkeypatch.setattr(import_page_module, "show_toast", lambda *args, **kwargs: None)
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    page = ImportPage([], storage)
    page.extraction_result = SimpleNamespace(combined_content=SimpleNamespace(text="conteúdo"))
    events: list[str] = []
    page._generate_prompt = lambda: events.append("prompt")
    page._copy_prompt = lambda: events.append("copy")
    page._open_external_ai = lambda: events.append("open")

    page._finish_prepare_study_package()

    assert events == ["prompt", "copy", "open"]
