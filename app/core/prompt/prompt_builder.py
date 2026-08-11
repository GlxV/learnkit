from __future__ import annotations

from dataclasses import dataclass

from app.core.models.extracted_content import ExtractedContent


@dataclass(slots=True)
class PromptOptions:
    flashcard_count: int = 10
    question_count: int = 10
    difficulty: str = "medio"
    language_style: str = "direta para prova"
    summary_mode: str = "texto + visual avancado"
    visual_style: str = "auto"
    response_format: str = "json"


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
        if selected.response_format.strip().lower() in {"markdown", "legacy"}:
            return self._build_markdown_prompt(
                subject_name,
                module_name,
                block_title,
                extracted_content,
                selected,
            )
        return self._build_json_prompt(
            subject_name,
            module_name,
            block_title,
            extracted_content,
            selected,
        )

    def _build_json_prompt(
        self,
        subject_name: str,
        module_name: str,
        block_title: str,
        extracted_content: ExtractedContent,
        selected: PromptOptions,
    ) -> str:
        return f"""Voce e um assistente de estudos.

Transforme o conteudo fornecido em um pacote de estudo organizado para o LearnKit.

Contexto:
- Materia: {subject_name}
- Modulo: {module_name}
- Bloco de estudo: {block_title}
- Dificuldade desejada: {selected.difficulty}
- Linguagem: {selected.language_style}
- Tipo de resumo: {selected.summary_mode}
- Estilo visual do resumo: {selected.visual_style}

Regras obrigatorias:
- Use apenas o conteudo fornecido.
- Nao invente informacoes fora do material enviado.
- Responda exclusivamente com JSON valido, sem Markdown, comentarios ou cercas ``` .
- Use schema_version exatamente como "learnkit.study_package.v1".
- Gere ate {selected.flashcard_count} flashcards uteis.
- Gere ate {selected.question_count} perguntas de multipla escolha com 4 alternativas.
- O gabarito deve ser somente A, B, C ou D.
- Crie um resumo texto objetivo, com visao geral e topicos principais.
- Em summary_visual, gere um objeto JSON estruturado compativel com o LearnKit e inclua "style": "{selected.visual_style}".
- O resumo visual deve parecer uma apresentacao/mini-site de estudo premium, nao HTML simples.
- Use blocos variados no summary_visual, evitando concentrar tudo em section: hero, cards, callout,
  table, comparison, steps, timeline, mistakes, formula, flow ou chart quando fizer sentido.
- Tambem pode usar mindmap, concept_map, exam_trap, source_quote e quiz_preview quando o conteudo pedir.
- Variantes aceitas de callout: info, warning, danger, success, tip e exam.
- Charts devem ser apenas dados declarativos em JSON. Nunca envie codigo Python, HTML ou JS.
- Nao envie HTML bruto, CSS, scripts, iframes ou Markdown dentro de summary_visual.
- Evite texto gigante em um unico bloco; divida em blocos curtos, escaneaveis e memoraveis.
- Para items, use campos semanticos quando fizer sentido: term/definition, mistake/correction,
  step/title/text, name/formula, label/text. O LearnKit renderiza esses formatos diretamente.
- Se nao conseguir gerar resumo visual, use um objeto vazio em summary_visual.
- Direcao dos estilos: auto escolhe pelo conteudo; prova e limpo e focado em memorizacao;
  lab usa clima cientifico; neon usa azul/roxo/ciano premium; retro usa terminal/CRT sutil;
  minimalista e serio, claro e discreto.

Formato JSON esperado:

{{
  "schema_version": "learnkit.study_package.v1",
  "summary_text": "Resumo em Markdown simples, sem titulo de secao obrigatorio.",
  "summary_visual": {{
    "title": "{block_title}",
    "subtitle": "Resumo visual para revisao",
    "style": "{selected.visual_style}",
    "sections": [
      {{
        "type": "hero",
        "title": "Ideia principal",
        "text": "..."
      }},
      {{
        "type": "cards",
        "title": "Pontos importantes",
        "items": [
          {{"title": "...", "text": "..."}}
        ]
      }},
      {{
        "type": "callout",
        "variant": "exam",
        "title": "Atalho mental",
        "text": "..."
      }},
      {{
        "type": "table",
        "title": "Comparacao rapida",
        "headers": ["Conceito", "Quando usar"],
        "rows": [["...", "..."]]
      }},
      {{
        "type": "steps",
        "title": "Sequencia essencial",
        "items": [
          {{"step": 1, "title": "Primeiro passo", "text": "Explique o que acontece."}}
        ]
      }},
      {{
        "type": "mistakes",
        "title": "Erros comuns",
        "items": [
          {{"mistake": "Erro provavel.", "correction": "Como corrigir."}}
        ]
      }},
      {{
        "type": "flow",
        "title": "Fluxo do processo",
        "nodes": [
          {{"id": "a", "label": "Inicio"}},
          {{"id": "b", "label": "Resultado"}}
        ],
        "edges": [
          {{"from": "a", "to": "b"}}
        ]
      }},
      {{
        "type": "chart",
        "chart_type": "bar",
        "title": "Peso dos conceitos",
        "labels": ["Conceito A", "Conceito B"],
        "values": [80, 60],
        "unit": "relevancia",
        "description": "Grafico didatico para revisao.",
        "interpretation": "Leia o conceito A como prioridade maior na revisao."
      }},
      {{
        "type": "exam_trap",
        "title": "Pegadinha de prova",
        "text": "..."
      }},
      {{
        "type": "quiz_preview",
        "title": "Como pode cair",
        "items": [
          {{"title": "Pergunta provavel", "text": "Resposta esperada em uma frase."}}
        ]
      }}
    ]
  }},
  "flashcards": [
    {{"front": "Pergunta objetiva?", "back": "Resposta objetiva."}}
  ],
  "questions": [
    {{
      "statement": "Enunciado da pergunta?",
      "alternatives": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "correct_answer": "A",
      "explanation": "Explicacao curta."
    }}
  ]
}}

Conteudo fornecido:

{extracted_content.text.strip()}
""".strip() + "\n"

    def _build_markdown_prompt(
        self,
        subject_name: str,
        module_name: str,
        block_title: str,
        extracted_content: ExtractedContent,
        selected: PromptOptions,
    ) -> str:
        return f"""Voce e um assistente de estudos.

Transforme o conteudo fornecido em um pacote de estudo organizado para o LearnKit.

Contexto:
- Materia: {subject_name}
- Modulo: {module_name}
- Bloco de estudo: {block_title}
- Dificuldade desejada: {selected.difficulty}
- Linguagem: {selected.language_style}
- Tipo de resumo: {selected.summary_mode}
- Estilo visual do resumo: {selected.visual_style}

Regras obrigatorias:
- Use apenas o conteudo fornecido.
- Nao invente informacoes fora do material enviado.
- Responda em Markdown, exceto pelo bloco # RESUMO_VISUAL, que deve conter JSON puro quando solicitado.
- Nao mude os nomes das secoes principais.
- Use exatamente as secoes: # RESUMO_TEXTO, # RESUMO_VISUAL, # FLASHCARDS e # PERGUNTAS.
- Sempre use "Pergunta:" e "Resposta:" nos flashcards.
- Sempre use "Enunciado:", A), B), C), D), "Gabarito:" e "Explicacao:" nas perguntas.
- Gere ate {selected.flashcard_count} flashcards uteis. Se o conteudo for pequeno, gere menos, mas mantenha o formato.
- Gere ate {selected.question_count} perguntas de multipla escolha com 4 alternativas. Se o conteudo for pequeno, gere menos, mas mantenha o formato.
- O gabarito deve ser somente A, B, C ou D.
- Crie um resumo texto objetivo, com visao geral e topicos principais.
- Em # RESUMO_VISUAL, gere JSON estruturado compativel com o LearnKit e inclua "style": "{selected.visual_style}".
- O resumo visual deve parecer uma apresentacao/mini-site de estudo premium, nao HTML simples.
- Use blocos variados: hero, cards, callout, table, comparison, steps, timeline, mistakes,
  formula, flow e chart quando fizer sentido. Evite usar somente section.
- Tambem pode usar mindmap, concept_map, exam_trap, source_quote e quiz_preview.
- Variantes aceitas de callout: info, warning, danger, success, tip e exam.
- Charts devem ser apenas dados declarativos em JSON. Nunca envie codigo Python, HTML ou JS.
- Nao envie HTML bruto, CSS, scripts, iframes ou Markdown dentro de # RESUMO_VISUAL.
- Evite texto gigante em um unico bloco; divida em blocos curtos, escaneaveis e memoraveis.
- Para items, prefira campos semanticos: term/definition, mistake/correction, step/title/text,
  name/formula, label/text. Nao use "Item" quando houver conteudo especifico.
- Nao coloque Markdown, comentarios ou cercas ``` dentro de # RESUMO_VISUAL.
- Se nao conseguir gerar resumo visual, deixe # RESUMO_VISUAL vazio e preserve as outras secoes.
- Direcao dos estilos: auto escolhe pelo conteudo; prova e limpo e focado em memorizacao;
  lab usa clima cientifico; neon usa azul/roxo/ciano premium; retro usa terminal/CRT sutil;
  minimalista e serio, claro e discreto.

Formato exato esperado:

# RESUMO_TEXTO

## Visao geral

...

## Topicos principais

- ...
- ...
- ...

# RESUMO_VISUAL
{{
  "title": "{block_title}",
  "subtitle": "Resumo visual para revisao",
  "style": "{selected.visual_style}",
  "sections": [
    {{
      "type": "hero",
      "title": "Ideia principal",
      "text": "..."
    }},
    {{
      "type": "cards",
      "title": "Pontos importantes",
      "items": [
        {{"title": "...", "text": "..."}}
      ]
    }},
    {{
      "type": "callout",
      "variant": "warning",
      "title": "Atencao",
      "text": "..."
    }},
    {{
      "type": "definition",
      "title": "Conceito-chave",
      "term": "Termo",
      "definition": "Definicao direta."
    }},
    {{
      "type": "mistakes",
      "title": "Erros comuns",
      "items": [
        {{"mistake": "Erro provavel.", "correction": "Como corrigir."}}
      ]
    }},
    {{
      "type": "flow",
      "title": "Fluxo",
      "nodes": [
        {{"id": "a", "label": "Inicio"}},
        {{"id": "b", "label": "Fim"}}
      ],
      "edges": [
        {{"from": "a", "to": "b"}}
      ]
    }},
    {{
      "type": "chart",
      "chart_type": "horizontal_bar",
      "title": "Comparacao didatica",
      "labels": ["A", "B", "C"],
      "values": [90, 70, 50],
      "unit": "pontuacao",
      "description": "Use somente dados declarativos.",
      "interpretation": "Explique em uma frase como revisar este grafico."
    }},
    {{
      "type": "exam_trap",
      "title": "Pegadinha de prova",
      "text": "..."
    }},
    {{
      "type": "quiz_preview",
      "title": "Como pode cair",
      "items": [
        {{"title": "Pergunta provavel", "text": "Resposta esperada em uma frase."}}
      ]
    }}
  ]
}}

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
