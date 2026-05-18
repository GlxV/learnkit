from __future__ import annotations

import json
from pathlib import Path

from app.application.dto.visual_summary import (
    dump_visual_summary,
    parse_visual_summary,
    visual_summary_slides,
)


def test_parse_visual_summary_normalizes_supported_blocks() -> None:
    summary = parse_visual_summary(
        {
            "title": "Estruturas",
            "subtitle": "Revisao",
            "sections": [
                {"type": "hero", "title": "Ideia central", "text": "Organizar dados."},
                {"type": "comparison", "items": [{"title": "Array", "text": "Indice direto"}]},
                {"type": "chart", "chart_type": "bar", "labels": ["Array"], "values": [90]},
            ],
        }
    )

    assert summary is not None
    assert summary["title"] == "Estruturas"
    assert [section["type"] for section in summary["sections"]] == [
        "hero",
        "comparison",
        "chart",
    ]
    assert summary["sections"][2]["values"] == [90.0]


def test_parse_visual_summary_keeps_unknown_type_as_generic_section() -> None:
    summary = parse_visual_summary(
        '{"title":"Teste","sections":[{"type":"unknown","title":"X","content":"Texto"}]}'
    )

    assert summary is not None
    assert summary["sections"][0]["type"] == "section"
    assert summary["sections"][0]["text"] == "Texto"


def test_parse_visual_summary_accepts_incomplete_chart_without_breaking() -> None:
    summary = parse_visual_summary(
        {"title": "Teste", "sections": [{"type": "chart", "title": "Sem dados"}]}
    )

    assert summary is not None
    chart = summary["sections"][0]
    assert chart["type"] == "chart"
    assert chart["chart_type"] == "bar"
    assert chart["labels"] == []
    assert chart["values"] == []


def test_visual_summary_slides_adds_opening_slide_when_needed() -> None:
    summary = parse_visual_summary(
        {"title": "Teste", "subtitle": "Resumo", "sections": [{"type": "table"}]}
    )

    slides = visual_summary_slides(summary)

    assert [slide["type"] for slide in slides] == ["hero", "table"]
    assert slides[0]["title"] == "Teste"


def test_mistakes_items_keep_mistake_and_correction_text() -> None:
    summary = parse_visual_summary(
        {
            "title": "Teste",
            "sections": [
                {
                    "type": "mistakes",
                    "title": "Erros comuns",
                    "items": [
                        {
                            "mistake": "Confundir fila com pilha.",
                            "correction": "Fila remove pelo inicio e pilha remove pelo topo.",
                        }
                    ],
                }
            ],
        }
    )

    item = summary["sections"][0]["items"][0]  # type: ignore[index]
    assert item["title"] == "Confundir fila com pilha."
    assert item["text"] == "Fila remove pelo inicio e pilha remove pelo topo."
    assert item["title"] != "Item"


def test_steps_items_keep_number_title_and_text() -> None:
    summary = parse_visual_summary(
        {
            "title": "Teste",
            "sections": [
                {
                    "type": "steps",
                    "items": [
                        {
                            "step": 1,
                            "title": "Inserir 15",
                            "text": "O valor 15 entra primeiro e se torna a raiz.",
                        }
                    ],
                }
            ],
        }
    )

    item = summary["sections"][0]["items"][0]  # type: ignore[index]
    assert item["number"] == "1"
    assert item["title"] == "Inserir 15"
    assert item["text"] == "O valor 15 entra primeiro e se torna a raiz."


def test_flow_nodes_and_edges_become_linear_items() -> None:
    summary = parse_visual_summary(
        {
            "title": "Teste",
            "sections": [
                {
                    "type": "flow",
                    "nodes": [
                        {"id": "head", "label": "Cabeca"},
                        {"id": "node1", "label": "No: dado + proximo"},
                        {"id": "null", "label": "None / Nulo"},
                    ],
                    "edges": [
                        {"from": "head", "to": "node1"},
                        {"from": "node1", "to": "null"},
                    ],
                }
            ],
        }
    )

    assert summary["sections"][0]["items"] == ["Cabeca", "No: dado + proximo", "None / Nulo"]  # type: ignore[index]


def test_comparison_left_right_shape_becomes_renderable_items() -> None:
    summary = parse_visual_summary(
        {
            "title": "Teste",
            "sections": [
                {
                    "type": "comparison",
                    "left": {"title": "Fila", "items": ["FIFO", "Remove pelo inicio"]},
                    "right": {"title": "Pilha", "items": ["LIFO", "Remove pelo topo"]},
                }
            ],
        }
    )

    items = summary["sections"][0]["items"]  # type: ignore[index]
    assert items[0]["title"] == "Fila"
    assert items[0]["points"] == ["FIFO", "Remove pelo inicio"]
    assert items[1]["title"] == "Pilha"


def test_formula_example_and_definition_items_are_preserved() -> None:
    summary = parse_visual_summary(
        {
            "title": "Teste",
            "sections": [
                {
                    "type": "formula",
                    "items": [{"name": "Fila", "formula": "FIFO = First In, First Out"}],
                },
                {
                    "type": "example",
                    "items": [{"title": "Array", "text": "Acesso direto ao item 5."}],
                },
                {
                    "type": "definition",
                    "term": "Estrutura de Dados",
                    "definition": "Maneira especifica de organizar dados.",
                },
            ],
        }
    )

    formula, example, definition = summary["sections"]  # type: ignore[index]
    assert formula["items"][0]["title"] == "Fila"
    assert formula["items"][0]["text"] == "FIFO = First In, First Out"
    assert example["items"][0]["title"] == "Array"
    assert definition["items"][0]["title"] == "Estrutura de Dados"
    assert definition["items"][0]["text"] == "Maneira especifica de organizar dados."


def test_dump_visual_summary_keeps_empty_object_empty() -> None:
    assert dump_visual_summary({}) == ""


def test_dump_visual_summary_returns_normalized_json() -> None:
    dumped = dump_visual_summary(
        {
            "title": "Teste",
            "sections": [
                {
                    "type": "mistakes",
                    "items": [{"mistake": "Erro", "correction": "Correcao"}],
                }
            ],
        }
    )

    assert '"title": "Erro"' in dumped
    assert '"text": "Correcao"' in dumped


def test_rich_visual_fixture_covers_all_supported_block_types() -> None:
    package = json.loads(Path("tests/fixtures/rich_visual_study_package.json").read_text(encoding="utf-8"))
    summary = parse_visual_summary(package["summary_visual"])

    types = {section["type"] for section in summary["sections"]}  # type: ignore[index]
    assert {
        "hero",
        "section",
        "cards",
        "callout",
        "table",
        "comparison",
        "steps",
        "timeline",
        "tags",
        "formula",
        "definition",
        "example",
        "mistakes",
        "flow",
        "chart",
    }.issubset(types)
