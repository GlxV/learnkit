import json
import os
import sys


def _qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def test_sidebar_hides_database_by_default_and_can_toggle() -> None:
    _qapp()

    from app.ui.components.sidebar import Sidebar

    sidebar = Sidebar()

    assert "database" not in sidebar.visible_item_keys()

    sidebar.set_developer_mode(True)
    assert sidebar.visible_item_keys() == [
        "home",
        "subjects",
        "studies",
        "reviews",
        "flashcards",
        "questions",
        "progress",
        "database",
        "import",
        "settings",
    ]

    sidebar.set_developer_mode(False)
    assert "database" not in sidebar.visible_item_keys()


def test_main_window_defaults_developer_mode_to_false_when_settings_missing(tmp_path, monkeypatch) -> None:
    _qapp()
    monkeypatch.chdir(tmp_path)

    from app.ui.main_window import MainWindow

    window = MainWindow()

    assert window.developer_mode is False
    assert "database" not in window.sidebar.visible_item_keys()

    window.navigate("database")
    assert window.stack.currentWidget() is window.pages["home"]


def test_main_window_shows_database_when_developer_mode_is_true(tmp_path, monkeypatch) -> None:
    _qapp()
    monkeypatch.chdir(tmp_path)
    settings_path = tmp_path / "data" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(json.dumps({"developer_mode": True}), encoding="utf-8")

    from app.ui.main_window import MainWindow

    window = MainWindow()

    assert window.developer_mode is True
    assert "database" in window.sidebar.visible_item_keys()

    window.navigate("database")
    assert window.stack.currentWidget() is window.pages["database"]


def test_disabling_developer_mode_redirects_away_from_database(tmp_path, monkeypatch) -> None:
    _qapp()
    monkeypatch.chdir(tmp_path)
    settings_path = tmp_path / "data" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(json.dumps({"developer_mode": True}), encoding="utf-8")

    from app.ui.main_window import MainWindow

    window = MainWindow()
    window.navigate("database")
    assert window.stack.currentWidget() is window.pages["database"]

    settings_page = window.pages["settings"]
    settings_page.developer_mode.setChecked(False)

    assert window.developer_mode is False
    assert "database" not in window.sidebar.visible_item_keys()
    assert window.stack.currentWidget() is window.pages["settings"]


def test_main_window_invalid_settings_defaults_developer_mode_to_false(tmp_path, monkeypatch) -> None:
    _qapp()
    monkeypatch.chdir(tmp_path)
    settings_path = tmp_path / "data" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text("{invalid", encoding="utf-8")

    from app.ui.main_window import MainWindow

    window = MainWindow()

    assert window.developer_mode is False
    assert "database" not in window.sidebar.visible_item_keys()


def test_settings_page_developer_mode_toggle_persists_and_emits(tmp_path, monkeypatch) -> None:
    _qapp()

    from app.core.database.sqlite_storage import SQLiteStorage
    import app.ui.pages.settings_page as settings_module
    from app.ui.pages.settings_page import SettingsPage

    monkeypatch.setattr(settings_module, "show_toast", lambda *args, **kwargs: None)
    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    page = SettingsPage(storage)
    saved: list[dict[str, object]] = []
    page.settings_saved.connect(lambda settings: saved.append(dict(settings)))

    page.developer_mode.setChecked(True)

    settings = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert settings["developer_mode"] is True
    assert saved[-1]["developer_mode"] is True

    page.developer_mode.setChecked(False)

    settings = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert settings["developer_mode"] is False
    assert saved[-1]["developer_mode"] is False
