from __future__ import annotations

from pathlib import Path
import re
import tempfile

import fitz

from app.core.extractors.ocr_extractor import OcrExtractor, SupportsOcr


class PdfExtractor:
    def __init__(self, ocr_extractor: SupportsOcr | None = None) -> None:
        self.ocr_extractor = ocr_extractor or OcrExtractor()

    def extract_text(self, file_path: str | Path) -> str:
        return self.extract(file_path)[0]

    def extract(self, file_path: str | Path) -> tuple[str, list[str], int]:
        path = Path(file_path)
        parts: list[str] = []
        warnings: list[str] = []
        with fitz.open(path) as document:
            page_count = document.page_count
            low_text_pages = 0
            for page_index, page in enumerate(document, start=1):
                text = page.get_text("text").strip()
                if len(text) < 20:
                    block_text = "\n".join(
                        block[4].strip()
                        for block in page.get_text("blocks")
                        if len(block) >= 5 and str(block[4]).strip()
                    )
                    text = block_text.strip() or text
                text = self._clean_text(text)
                has_images = bool(page.get_images(full=True))
                should_try_ocr = len(text) < 120 or (has_images and len(text) < 500)
                if should_try_ocr:
                    ocr_text = self._extract_page_ocr(page)
                    if ocr_text and ocr_text not in text:
                        text = self._clean_text(
                            "\n\n".join(part for part in [text, "Texto OCR:\n" + ocr_text] if part)
                        )
                    elif has_images and not self.ocr_extractor.available:
                        warnings.append(
                            f"Pagina {page_index}: contem imagem, mas OCR local nao esta disponivel."
                        )
                if len(text) < 20:
                    low_text_pages += 1
                    warnings.append(
                        f"Pagina {page_index}: possivel pagina escaneada ou sem texto selecionavel."
                    )
                if text:
                    parts.append(f"## Pagina {page_index}\n\n{text}")

        if page_count and low_text_pages / page_count >= 0.6:
            warnings.append(
                "O PDF pode ser escaneado: muitas paginas possuem pouco texto selecionavel."
            )
        return "\n\n".join(parts).strip(), warnings, page_count

    def _clean_text(self, text: str) -> str:
        text = text.replace("\x00", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _extract_page_ocr(self, page: fitz.Page) -> str:
        if not self.ocr_extractor.available:
            return ""
        try:
            with tempfile.TemporaryDirectory() as tmp:
                image_path = Path(tmp) / "page.png"
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                pixmap.save(image_path)
                return self.ocr_extractor.extract_image_file(image_path)
        except Exception:
            return ""
