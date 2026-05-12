from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from app.core.extractors.ocr_extractor import OcrExtractor, SupportsOcr


class DocxExtractor:
    WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

    def __init__(self, ocr_extractor: SupportsOcr | None = None) -> None:
        self.ocr_extractor = ocr_extractor or OcrExtractor()

    def extract_text(self, path: str | Path) -> str:
        text, _ = self.extract(path)
        return text

    def extract(self, path: str | Path) -> tuple[str, list[str]]:
        docx_path = Path(path)
        warnings: list[str] = []
        pieces: list[str] = []

        with zipfile.ZipFile(docx_path) as archive:
            document_names = [
                "word/document.xml",
                *sorted(name for name in archive.namelist() if name.startswith("word/header") and name.endswith(".xml")),
                *sorted(name for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml")),
            ]
            for document_name in document_names:
                if document_name not in archive.namelist():
                    continue
                xml = archive.read(document_name)
                try:
                    root = ElementTree.fromstring(xml)
                except ElementTree.ParseError:
                    warnings.append(f"Nao foi possivel ler {document_name}.")
                    continue
                pieces.extend(self._extract_paragraphs(root))
                tables = self._extract_tables(root)
                if tables:
                    pieces.append("\n\n".join(tables))
            image_texts = self._extract_images(archive, warnings)
            if image_texts:
                pieces.append("## Imagens no documento\n\n" + "\n\n".join(image_texts))

        text = self._clean_text("\n\n".join(piece for piece in pieces if piece.strip()))
        if not text:
            warnings.append("DOCX sem texto extraivel ou possivelmente composto apenas por imagens.")
        return text, warnings

    def _extract_paragraphs(self, root: ElementTree.Element) -> list[str]:
        paragraphs: list[str] = []
        for paragraph in root.iter(f"{self.WORD_NS}p"):
            text = self._text_from_node(paragraph)
            if text:
                paragraphs.append(text)
        return paragraphs

    def _extract_tables(self, root: ElementTree.Element) -> list[str]:
        tables: list[str] = []
        for table in root.iter(f"{self.WORD_NS}tbl"):
            rows: list[str] = []
            for row in table.iter(f"{self.WORD_NS}tr"):
                cells = [self._text_from_node(cell) for cell in row.iter(f"{self.WORD_NS}tc")]
                cells = [cell for cell in cells if cell]
                if cells:
                    rows.append(" | ".join(cells))
            if rows:
                tables.append("Tabela:\n" + "\n".join(rows))
        return tables

    def _text_from_node(self, node: ElementTree.Element) -> str:
        parts: list[str] = []
        for item in node.iter():
            if item.tag == f"{self.WORD_NS}t" and item.text:
                parts.append(item.text)
            elif item.tag == f"{self.WORD_NS}tab":
                parts.append("\t")
            elif item.tag in {f"{self.WORD_NS}br", f"{self.WORD_NS}cr"}:
                parts.append("\n")
        return self._clean_text("".join(parts))

    def _clean_text(self, text: str) -> str:
        text = text.replace("\x00", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _extract_images(self, archive: zipfile.ZipFile, warnings: list[str]) -> list[str]:
        image_names = [
            name
            for name in archive.namelist()
            if name.startswith("word/media/")
            and Path(name).suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
        ]
        if image_names and not self.ocr_extractor.available:
            warnings.append("DOCX contem imagem, mas OCR local nao esta disponivel.")
            return []

        image_texts: list[str] = []
        for index, image_name in enumerate(image_names, start=1):
            try:
                text = self.ocr_extractor.extract_image_bytes(
                    archive.read(image_name),
                    Path(image_name).suffix,
                ).strip()
            except Exception:
                text = ""
            if text:
                image_texts.append(f"Texto em imagem {index}:\n{text}")
        return image_texts
