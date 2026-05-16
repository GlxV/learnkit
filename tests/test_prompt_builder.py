from app.core.models.extracted_content import ExtractedContent
from app.core.prompt.prompt_builder import PromptBuilder, PromptOptions


def test_build_prompt_includes_structure_options_and_extracted_content() -> None:
    content = ExtractedContent(
        text="Texto sobre modelo relacional e chaves primarias.",
        source_files=["aula.pdf"],
    )
    options = PromptOptions(
        flashcard_count=5,
        question_count=3,
        difficulty="intermediario",
        language_style="clara",
    )

    prompt = PromptBuilder().build(
        subject_name="Banco de Dados",
        module_name="Prova 1",
        block_title="Modelo Relacional",
        extracted_content=content,
        options=options,
    )

    assert '"schema_version": "learnkit.study_package.v1"' in prompt
    assert '"summary_text"' in prompt
    assert '"summary_visual"' in prompt
    assert '"flashcards"' in prompt
    assert '"questions"' in prompt
    assert "5 flashcards" in prompt
    assert "3 perguntas" in prompt
    assert "intermediario" in prompt
    assert "Texto sobre modelo relacional" in prompt
    assert "Use apenas o conteudo fornecido" in prompt
    assert "Responda exclusivamente com JSON valido" in prompt


def test_build_prompt_keeps_markdown_legacy_format_when_requested() -> None:
    prompt = PromptBuilder().build(
        subject_name="Banco de Dados",
        module_name="Prova 1",
        block_title="Modelo Relacional",
        extracted_content=ExtractedContent(text="texto"),
        options=PromptOptions(response_format="markdown"),
    )

    assert "# RESUMO_TEXTO" in prompt
    assert "# RESUMO_VISUAL" in prompt
    assert "# FLASHCARDS" in prompt
    assert "# PERGUNTAS" in prompt
