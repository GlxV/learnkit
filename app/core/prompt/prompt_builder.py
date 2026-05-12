from __future__ import annotations

from dataclasses import dataclass

from app.core.models.extracted_content import ExtractedContent


@dataclass(slots=True)
class PromptOptions:
    flashcard_count: int = 10
    question_count: int = 10
    difficulty: str = "medio"
    language_style: str = "direta para prova"


class PromptBuilder:
    def build(
        self,
        subject_name: str,
        module_name: str,
        block_title: str,
        extracted_content: ExtractedContent,
        options: PromptOptions | None = None,
    ) -> str:
        selected = options or PromptOptions()
        return f"""Voce e um assistente de estudos.

Transforme o conteudo fornecido em um pacote de estudo organizado para o LearnKit.

Contexto:
- Materia: {subject_name}
- Modulo: {module_name}
- Bloco de estudo: {block_title}
- Dificuldade desejada: {selected.difficulty}
- Linguagem: {selected.language_style}

Regras obrigatorias:
- Use apenas o conteudo fornecido.
- Nao invente informacoes fora do material enviado.
- Nao use JSON nesta versao.
- Responda somente em Markdown.
- Nao mude os nomes das secoes principais.
- Use exatamente as secoes: # RESUMO, # FLASHCARDS e # PERGUNTAS.
- Sempre use "Pergunta:" e "Resposta:" nos flashcards.
- Sempre use "Enunciado:", A), B), C), D), "Gabarito:" e "Explicacao:" nas perguntas.
- Gere ate {selected.flashcard_count} flashcards uteis. Se o conteudo for pequeno, gere menos, mas mantenha o formato.
- Gere ate {selected.question_count} perguntas de multipla escolha com 4 alternativas. Se o conteudo for pequeno, gere menos, mas mantenha o formato.
- O gabarito deve ser somente A, B, C ou D.
- Crie um resumo objetivo, com visao geral e topicos principais.

Formato exato esperado:

# RESUMO

## Visao geral

...

## Topicos principais

- ...
- ...
- ...

# FLASHCARDS

## Card 1
Pergunta: ...
Resposta: ...

## Card 2
Pergunta: ...
Resposta: ...

# PERGUNTAS

## Pergunta 1
Enunciado: ...
A) ...
B) ...
C) ...
D) ...
Gabarito: A
Explicacao: ...

## Pergunta 2
Enunciado: ...
A) ...
B) ...
C) ...
D) ...
Gabarito: C
Explicacao: ...

Conteudo fornecido:

{extracted_content.text.strip()}
""".strip() + "\n"
