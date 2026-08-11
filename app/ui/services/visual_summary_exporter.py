from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QImage, QPainter, QPdfWriter, QPageSize
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from app.application.dto.visual_summary import parse_visual_summary
from app.ui.components.summary_visual import SummaryVisualRenderer
from app.ui.theme import COLORS


class VisualSummaryExportService:
    """Render the declarative summary with the same renderer used by the UI."""

    def render_image(
        self,
        summary_visual: str,
        *,
        width: int = 1280,
        presentation: bool = True,
    ) -> QImage:
        if QApplication.instance() is None:
            raise RuntimeError("Visual summary export requires a QApplication.")
        data = parse_visual_summary(summary_visual)
        if data is None:
            raise ValueError("Resumo visual inválido ou vazio.")
        if width < 480:
            raise ValueError("A largura mínima de exportação é 480 pixels.")

        canvas = QWidget()
        canvas.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        canvas.setStyleSheet(f"background: {COLORS['background']};")
        layout = QVBoxLayout(canvas)
        margin = 34 if presentation else 22
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(20 if presentation else 14)
        SummaryVisualRenderer(
            presentation=presentation,
            style=data.get("style"),
        ).render_summary(layout, data)

        canvas.setFixedWidth(width)
        canvas.ensurePolished()
        layout.activate()
        canvas.adjustSize()
        height = max(canvas.sizeHint().height(), margin * 2 + 1)
        canvas.resize(width, height)
        layout.activate()

        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(COLORS["background"])
        painter = QPainter(image)
        canvas.render(painter, QPoint(0, 0))
        painter.end()
        canvas.deleteLater()
        return image

    def save_png(self, summary_visual: str, path: str | Path, *, width: int = 1280) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        image = self.render_image(summary_visual, width=width)
        if not image.save(str(target), "PNG"):
            raise OSError(f"Não foi possível salvar PNG: {target}")
        return target

    def save_pdf(self, summary_visual: str, path: str | Path, *, width: int = 1280) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        image = self.render_image(summary_visual, width=width)

        pdf = QPdfWriter(str(target))
        pdf.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        pdf.setResolution(144)
        painter = QPainter(pdf)
        try:
            page_width = max(pdf.width(), 1)
            page_height = max(pdf.height(), 1)
            source_page_height = max(1, int(image.width() * page_height / page_width))
            offset = 0
            while offset < image.height():
                crop_height = min(source_page_height, image.height() - offset)
                crop = image.copy(0, offset, image.width(), crop_height)
                destination = QRectF(0, 0, page_width, crop_height * page_width / image.width())
                painter.drawImage(destination, crop)
                offset += crop_height
                if offset < image.height():
                    pdf.newPage()
        finally:
            painter.end()
        return target
