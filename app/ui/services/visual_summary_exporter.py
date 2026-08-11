from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QImage, QPainter, QPdfWriter, QPageSize
from PySide6.QtWidgets import QApplication, QTableWidget, QVBoxLayout, QWidget

from app.application.dto.visual_summary import parse_visual_summary
from app.ui.components.summary_visual import SummaryVisualRenderer
from app.ui.theme import COLORS


class VisualSummaryExportService:
    """Render the declarative summary with the same renderer used by the UI."""

    MAX_EXPORT_PIXELS = 32_000_000
    EXPORT_DPI = 144

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
        canvas.resize(width, max(canvas.sizeHint().height(), margin * 2 + 1))
        layout.activate()
        self._expand_tables(canvas)
        layout.invalidate()
        layout.activate()
        canvas.adjustSize()
        height = max(canvas.sizeHint().height(), margin * 2 + 1)
        canvas.resize(width, height)
        layout.activate()

        if width * height > self.MAX_EXPORT_PIXELS:
            canvas.deleteLater()
            raise ValueError(
                "Resumo visual grande demais para exportar como bitmap com segurança."
            )

        image = QImage(width, height, QImage.Format.Format_ARGB32)
        if image.isNull():
            canvas.deleteLater()
            raise OSError("Não foi possível alocar a imagem do resumo visual.")
        dots_per_meter = round(self.EXPORT_DPI / 0.0254)
        image.setDotsPerMeterX(dots_per_meter)
        image.setDotsPerMeterY(dots_per_meter)
        image.fill(COLORS["background"])
        painter = QPainter()
        try:
            if not painter.begin(image):
                raise OSError("Não foi possível iniciar a renderização da imagem.")
            canvas.render(painter, QPoint(0, 0))
        finally:
            if painter.isActive():
                painter.end()
            canvas.deleteLater()
        return image

    def _expand_tables(self, canvas: QWidget) -> None:
        for table in canvas.findChildren(QTableWidget):
            table.resizeRowsToContents()
            content_height = sum(table.rowHeight(row) for row in range(table.rowCount()))
            header_height = table.horizontalHeader().height()
            frame_height = table.frameWidth() * 2
            table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            table.setFixedHeight(header_height + content_height + frame_height + 4)
            table.doItemsLayout()

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
        pdf.setResolution(self.EXPORT_DPI)
        painter = QPainter()
        try:
            if not painter.begin(pdf):
                raise OSError(f"Não foi possível iniciar a gravação do PDF: {target}")
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
                if offset < image.height() and not pdf.newPage():
                    raise OSError(f"Não foi possível criar uma nova página no PDF: {target}")
        finally:
            if painter.isActive():
                painter.end()
        if not target.is_file() or target.stat().st_size <= 0:
            raise OSError(f"Não foi possível salvar PDF: {target}")
        return target
