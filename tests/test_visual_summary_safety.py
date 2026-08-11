from __future__ import annotations

import json
import os
import sys


def _qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def test_visual_text_helpers_force_plain_text() -> None:
    _qapp()
    from PySide6.QtCore import Qt

    from app.ui.components.summary_visual import _body, _chip, _title

    for widget in (
        _body("<b>conteudo</b>"),
        _title("<i>titulo</i>"),
        _chip("<img src=x>", "#ffffff"),
    ):
        assert widget.textFormat() == Qt.TextFormat.PlainText


def test_formula_and_quote_content_are_plain_text() -> None:
    _qapp()
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

    from app.ui.components.summary_visual import SummaryVisualRenderer

    host = QWidget()
    layout = QVBoxLayout(host)
    payload = "<img src='file:///C:/secret.png'>"
    data = {
        "title": "Teste",
        "sections": [
            {"type": "formula", "title": "Formula", "text": payload},
            {"type": "source_quote", "title": "Fonte", "quote": payload},
        ],
    }
    SummaryVisualRenderer().render_summary(layout, data)

    payload_labels = [label for label in host.findChildren(QLabel) if payload in label.text()]
    assert len(payload_labels) == 2
    assert all(label.textFormat() == Qt.TextFormat.PlainText for label in payload_labels)


def test_horizontal_chart_height_scales_with_row_count() -> None:
    _qapp()
    from app.ui.components.summary_visual import ChartWidget

    chart = ChartWidget(
        {
            "chart_type": "horizontal_bar",
            "labels": [str(index) for index in range(20)],
            "values": list(range(20)),
        }
    )

    assert chart.sizeHint().height() >= 20 * 32 + 40
    assert chart.minimumHeight() == chart.sizeHint().height()


def test_presentation_restores_maximized_state_after_fullscreen() -> None:
    app = _qapp()
    from app.ui.components.summary_visual import PresentationDialog

    visual = json.dumps(
        {"title": "Resumo", "sections": [{"type": "hero", "title": "Slide"}]}
    )
    dialog = PresentationDialog("Resumo", visual)
    dialog.showMaximized()
    app.processEvents()
    assert dialog.isMaximized()

    dialog._toggle_fullscreen()
    app.processEvents()
    assert dialog.isFullScreen()
    dialog._toggle_fullscreen()
    app.processEvents()

    assert dialog.isMaximized()
    dialog.close()
