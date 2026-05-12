from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from app.core.extractors.docx_extractor import DocxExtractor
from app.core.extractors.ocr_extractor import OcrExtractor
from app.core.extractors.pdf_extractor import PdfExtractor
from app.core.extractors.pptx_extractor import PptxExtractor
from app.core.models.extracted_content import ExtractedContent
from app.core.models.imported_file import ImportedFile


@dataclass(slots=True)
class ExtractedFileResult:
    imported_file: ImportedFile
    text: str = ""
    character_count: int = 0
    word_count: int = 0
    page_count: int | None = None
    slide_count: int | None = None
    extraction_warnings: list[str] = field(default_factory=list)
    error_message: str | None = None


@dataclass(slots=True)
class FileExtractionResult:
    files: list[ExtractedFileResult] = field(default_factory=list)
    combined_content: ExtractedContent = field(default_factory=ExtractedContent)
    file_texts: dict[str, str] = field(default_factory=dict)


class FileExtractor:
    TEXT_EXTENSIONS = {
        "txt",
        "md",
        "markdown",
        "js",
        "ts",
        "py",
        "java",
        "c",
        "cpp",
        "cs",
        "html",
        "htm",
        "css",
        "json",
        "csv",
        "xml",
        "yaml",
        "yml",
        "sql",
    }

    def __init__(
        self,
        pdf_extractor: PdfExtractor | None = None,
        pptx_extractor: PptxExtractor | None = None,
        docx_extractor: DocxExtractor | None = None,
    ) -> None:
        ocr_extractor = OcrExtractor()
        self.pdf_extractor = pdf_extractor or PdfExtractor(ocr_extractor)
        self.pptx_extractor = pptx_extractor or PptxExtractor(ocr_extractor)
        self.docx_extractor = docx_extractor or DocxExtractor(ocr_extractor)

    def extract_files(self, file_paths: list[str | Path]) -> FileExtractionResult:
        results: list[ExtractedFileResult] = []
        file_texts: dict[str, str] = {}

        for raw_path in file_paths:
            path = Path(raw_path)
            result = self._extract_one(path)
            results.append(result)
            if result.error_message is None:
                file_texts[result.imported_file.file_name] = result.text

        combined_text = self._combined_markdown(file_texts)
        return FileExtractionResult(
            files=results,
            combined_content=ExtractedContent(
                text=combined_text,
                source_files=list(file_texts.keys()),
            ),
            file_texts=file_texts,
        )

    def export_extracted_text(
        self,
        extraction: FileExtractionResult,
        output_path: str | Path,
        file_format: str = "md",
    ) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        normalized = file_format.lower().lstrip(".")
        file_texts = extraction.file_texts

        if normalized == "md":
            content = self._combined_markdown(file_texts)
        elif normalized == "txt":
            content = self._combined_text(file_texts)
        else:
            raise ValueError("Formato de exportacao nao suportado. Use 'md' ou 'txt'.")

        path.write_text(content, encoding="utf-8")
        return path

    def export_block_text(
        self,
        source_files: list[str],
        text: str,
        output_path: str | Path,
        file_format: str = "md",
    ) -> Path:
        if source_files:
            file_texts = {", ".join(source_files): text}
        else:
            file_texts = {"conteudo_extraido": text}
        return self.export_extracted_text(
            FileExtractionResult(file_texts=file_texts),
            output_path,
            file_format,
        )

    def _extract_one(self, path: Path) -> ExtractedFileResult:
        file_type = path.suffix.lower().lstrip(".")
        file_size = path.stat().st_size if path.exists() else 0
        imported_file = ImportedFile(
            original_path=str(path),
            file_name=path.name,
            file_type=file_type,
            file_size=file_size,
            extraction_status="pending",
        )

        try:
            if not path.exists():
                raise FileNotFoundError("Arquivo nao encontrado.")
            warnings: list[str] = []
            page_count: int | None = None
            slide_count: int | None = None
            if file_type == "pdf":
                text, warnings, page_count = self.pdf_extractor.extract(path)
            elif file_type == "pptx":
                text, warnings, slide_count = self.pptx_extractor.extract(path)
            elif file_type == "docx":
                text, warnings = self.docx_extractor.extract(path)
            elif file_type in self.TEXT_EXTENSIONS:
                text = self._clean_text(path.read_text(encoding="utf-8", errors="replace"))
            else:
                raise ValueError(
                    "Tipo de arquivo nao suportado. Use PDF, PPTX, DOCX, TXT, MD "
                    "ou arquivos de codigo/texto comuns."
                )

            imported_file.extraction_status = "success"
            imported_file.page_count = page_count
            imported_file.slide_count = slide_count
            imported_file.extraction_warnings = warnings
            return ExtractedFileResult(
                imported_file=imported_file,
                text=text,
                character_count=len(text),
                word_count=len(text.split()),
                page_count=page_count,
                slide_count=slide_count,
                extraction_warnings=warnings,
            )
        except Exception as exc:
            imported_file.extraction_status = "failed"
            imported_file.error_message = str(exc)
            return ExtractedFileResult(
                imported_file=imported_file,
                error_message=str(exc),
            )

    def _combined_markdown(self, file_texts: dict[str, str]) -> str:
        parts = ["# Conteudo extraido"]
        for file_name, text in file_texts.items():
            parts.append(f"## Arquivo: {file_name}\n\n{text.strip()}")
        return "\n\n".join(parts).strip() + "\n"

    def _clean_text(self, text: str) -> str:
        text = text.replace("\x00", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _combined_text(self, file_texts: dict[str, str]) -> str:
        parts = ["Conteudo extraido"]
        for file_name, text in file_texts.items():
            parts.append(f"Arquivo: {file_name}\n\n{text.strip()}")
        return "\n\n".join(parts).strip() + "\n"
