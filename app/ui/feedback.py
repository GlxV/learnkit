from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox, QPushButton, QWidget


LOG_PATH = Path("app/logs/learnkit.log")


def get_logger() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("learnkit")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger


def log_action(event: str, **metadata: object) -> None:
    safe = " ".join(f"{key}={value}" for key, value in metadata.items())
    get_logger().info("%s %s", event, safe)


def show_toast(widget: QWidget, message: str, kind: str = "info") -> None:
    window = widget.window()
    if hasattr(window, "show_toast"):
        window.show_toast(message, kind)
        return
    QMessageBox.information(widget, "LearnKit", message)


def confirm_action(widget: QWidget, title: str, message: str) -> bool:
    window = widget.window()
    if hasattr(window, "confirm_action"):
        return bool(window.confirm_action(title, message))
    return QMessageBox.question(widget, title, message) == QMessageBox.StandardButton.Yes


def future_action(widget: QWidget, feature: str) -> None:
    log_action("future_action_clicked", feature=feature)
    QMessageBox.information(widget, "Recurso futuro", f"{feature} ficara disponivel em uma versao futura.")


def set_button_loading(button: QPushButton, loading: bool = True, text: str = "Carregando...") -> None:
    if loading:
        if button.property("learnkit_original_text") is None:
            button.setProperty("learnkit_original_text", button.text())
        button.setEnabled(False)
        button.setText(text)
        return

    original = button.property("learnkit_original_text")
    if original:
        button.setText(str(original))
    button.setProperty("learnkit_original_text", None)
    button.setEnabled(True)


def flash_button_success(button: QPushButton, text: str = "Pronto!", delay_ms: int = 1400) -> None:
    original = button.property("learnkit_original_text") or button.text()
    button.setProperty("learnkit_original_text", original)
    button.setText(text)
    button.setEnabled(False)

    def restore() -> None:
        button.setText(str(original))
        button.setEnabled(True)
        button.setProperty("learnkit_original_text", None)

    QTimer.singleShot(delay_ms, restore)
