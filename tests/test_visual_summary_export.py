from __future__ import annotations

import os
import json
import sys
from pathlib import Path


def _qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def test_visual_summary_export_renders_same_summary_to_png_and_multipage_pdf(tmp_path: Path) -> None:
    _qapp()
    from PySide6.QtGui import QImage

    from app.ui.services.visual_summary_exporter import VisualSummaryExportService

    data = {
        "title": "Estruturas",
        "style": "prova",
        "sections": [
            {"type": "hero", "title": "Ideia central", "text": "Resumo para prova."},
            {"type": "exam_trap", "title": "Pegadinha", "text": "Não confunda as estruturas."},
        ],
    }
    data["sections"].extend(
        {
            "type": "cards",
            "title": f"Pontos {index}",
            "items": [
                {"title": "Array", "text": "Acesso indexado."},
                {"title": "Lista", "text": "Nós encadeados."},
                {"title": "Fila", "text": "Processamento FIFO."},
            ],
        }
        for index in range(8)
    )
    visual = json.dumps(data, ensure_ascii=False)
    service = VisualSummaryExportService()
    image = service.render_image(visual, width=900)
    png = service.save_png(visual, tmp_path / "summary.png", width=900)
    pdf = service.save_pdf(visual, tmp_path / "summary.pdf", width=900)

    assert image.width() == 900
    assert image.height() > image.width()
    assert png.exists() and png.stat().st_size > 100
    assert pdf.exists() and pdf.stat().st_size > 100
    loaded = QImage(str(png))
    assert not loaded.isNull()


def test_visual_summary_export_rejects_invalid_summary(tmp_path: Path) -> None:
    _qapp()
    import pytest

    from app.ui.services.visual_summary_exporter import VisualSummaryExportService

    with pytest.raises(ValueError, match="inválido"):
        VisualSummaryExportService().save_png("{invalid", tmp_path / "bad.png")


def test_summary_dialog_exposes_rendered_visual_export_actions(tmp_path: Path) -> None:
    _qapp()
    from PySide6.QtWidgets import QPushButton

    from app.application.use_cases.manage_study_summary import ManageStudySummaryUseCase
    from app.core.database.sqlite_storage import SQLiteStorage
    from app.core.models.summary import Summary
    from app.ui.pages.studies_page import SummaryDialog
    from app.application.query_services.study_session_query_service import StudySessionQueryService

    storage = SQLiteStorage(tmp_path / "learnkit.db", migrate_json=False)
    subject = storage.create_subject("Biologia")
    module = storage.create_module(subject.slug, "Prova")
    block = storage.create_block(subject.slug, module.slug, "Celula")
    block.summary = Summary("Resumo textual")
    block.summary_visual = '{"title":"Celula","sections":[{"type":"hero","title":"Nucleo"}]}'
    storage.save_block(subject, module, block)

    dialog = SummaryDialog(
        StudySessionQueryService(storage),
        ManageStudySummaryUseCase(storage),
        block.id,
    )
    buttons = {button.text(): button for button in dialog.findChildren(QPushButton)}

    assert buttons["Copiar imagem"].isEnabled()
    assert buttons["Salvar PNG"].isEnabled()
    assert buttons["Salvar PDF"].isEnabled()
    dialog.close()
