from pathlib import Path
import zipfile

from app.core.extractors.file_extractor import FileExtractor


def test_extract_txt_and_markdown_files(tmp_path: Path) -> None:
    txt_path = tmp_path / "aula.txt"
    txt_path.write_text("Linha 1\n\nLinha 2 com conteudo.", encoding="utf-8")
    md_path = tmp_path / "resumo.md"
    md_path.write_text("# Titulo\n\n- item importante", encoding="utf-8")

    result = FileExtractor().extract_files([txt_path, md_path])

    assert len(result.files) == 2
    assert all(item.error_message is None for item in result.files)
    assert "Linha 1" in result.combined_content.text
    assert "# Titulo" in result.combined_content.text
    assert result.files[0].character_count > 0
    assert result.files[1].word_count > 0


def test_extract_docx_file_with_stdlib_parser(tmp_path: Path) -> None:
    docx_path = tmp_path / "aula.docx"
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Modelo relacional</w:t></w:r></w:p>
    <w:p><w:r><w:t>Chaves primarias identificam registros.</w:t></w:r></w:p>
  </w:body>
</w:document>
"""
    with zipfile.ZipFile(docx_path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", document_xml)

    result = FileExtractor().extract_files([docx_path])

    assert result.files[0].error_message is None
    assert "Modelo relacional" in result.combined_content.text
    assert "Chaves primarias" in result.combined_content.text


def test_pdf_extraction_reports_low_text_warning(tmp_path: Path) -> None:
    import fitz

    pdf_path = tmp_path / "scan_like.pdf"
    document = fitz.open()
    document.new_page()
    document.save(pdf_path)
    document.close()

    result = FileExtractor().extract_files([pdf_path])

    assert result.files[0].error_message is None
    assert result.files[0].page_count == 1
    assert result.files[0].extraction_warnings
    assert "escaneada" in result.files[0].extraction_warnings[0].lower()
