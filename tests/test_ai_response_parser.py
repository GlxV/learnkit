from app.core.importer.ai_response_parser import AIResponseParser
from pathlib import Path


SAMPLE_RESPONSE = """# RESUMO

## Topicos principais

- Banco de dados organiza informacoes.
- Chaves primarias identificam registros.

# FLASHCARDS

## Card 1

Pergunta: O que e uma chave primaria?
Resposta: Um atributo que identifica unicamente um registro.

## Card 2

Pergunta: Para que serve uma tabela?
Resposta: Para organizar dados em linhas e colunas.

# PERGUNTAS

## Pergunta 1

Enunciado: Qual alternativa descreve uma chave primaria?

A) Um campo que aceita valores repetidos sempre
B) Um identificador unico de registros
C) Um arquivo de backup
D) Uma consulta SQL

Gabarito: B
Explicação: A chave primaria identifica cada registro de forma unica.
"""


def test_parse_structured_markdown_response() -> None:
    parsed = AIResponseParser().parse(SAMPLE_RESPONSE)

    assert parsed.ai_response.parsed_successfully is True
    assert parsed.warnings == []
    assert "Banco de dados organiza" in parsed.summary.content
    assert len(parsed.flashcards) == 2
    assert parsed.flashcards[0].question == "O que e uma chave primaria?"
    assert parsed.flashcards[0].answer.startswith("Um atributo")
    assert len(parsed.questions) == 1
    assert parsed.questions[0].statement == "Qual alternativa descreve uma chave primaria?"
    assert parsed.questions[0].alternatives["B"] == "Um identificador unico de registros"
    assert parsed.questions[0].correct_answer == "B"


def test_parser_returns_warnings_for_missing_sections() -> None:
    parsed = AIResponseParser().parse("# RESUMO\n\nTexto simples.")

    assert parsed.ai_response.parsed_successfully is False
    assert "Nenhuma secao FLASHCARDS encontrada." in parsed.warnings
    assert "Nenhuma secao PERGUNTAS encontrada." in parsed.warnings


def test_parser_accepts_text_and_visual_summary_sections() -> None:
    response = """# RESUMO_TEXTO

Resumo em Markdown.

# RESUMO_VISUAL
{
  "title": "Modelo Relacional",
  "sections": [
    {"type": "hero", "title": "Chaves", "text": "Identificam registros."}
  ]
}

# FLASHCARDS

## Card 1
Pergunta: O que e uma chave primaria?
Resposta: Identificador unico.

# PERGUNTAS

## Pergunta 1
Enunciado: Qual opcao define chave primaria?
A) Identificador unico
B) Backup
C) Grafico
D) Arquivo
Gabarito: A
Explicacao: Identifica registros.
"""

    parsed = AIResponseParser().parse(response)

    assert parsed.summary.content == "Resumo em Markdown."
    assert '"title": "Modelo Relacional"' in parsed.summary_visual
    assert parsed.ai_response.parsed_successfully is True


def test_parser_warns_and_ignores_invalid_visual_summary() -> None:
    response = """# RESUMO_TEXTO

Resumo.

# RESUMO_VISUAL
{invalid

# FLASHCARDS

# PERGUNTAS
"""

    parsed = AIResponseParser().parse(response)

    assert parsed.summary_visual == ""
    assert "RESUMO_VISUAL possui JSON invalido." in parsed.warnings


def test_parser_accepts_looser_markdown_variations() -> None:
    response = """# Resumo

Conteudo em linguagem livre.

# Flashcards

## Flashcard 1

- Pergunta: Qual e a formula geral?
- Resposta: f(x) = ax + b.

# Perguntas

## Questao 1

Enunciado: Qual alternativa mostra uma funcao linear?
A. f(x) = ax + b
B. x^2 + 4
C. raiz quadrada isolada
D. valor absoluto apenas
Resposta correta: A
Explicação: A forma ax + b representa uma funcao linear.
"""

    parsed = AIResponseParser().parse(response)

    assert parsed.ai_response.parsed_successfully is True
    assert parsed.flashcards[0].question == "Qual e a formula geral?"
    assert parsed.questions[0].alternatives["A"] == "f(x) = ax + b"
    assert parsed.questions[0].correct_answer == "A"
    assert parsed.questions[0].explanation == "A forma ax + b representa uma funcao linear."


def test_sample_fixture_has_expected_study_package() -> None:
    fixture = Path("tests/fixtures/sample_ai_response.md").read_text(encoding="utf-8")
    parsed = AIResponseParser().parse(fixture)

    assert parsed.ai_response.parsed_successfully is True
    assert parsed.summary.content
    assert len(parsed.flashcards) == 3
    assert len(parsed.questions) == 3
