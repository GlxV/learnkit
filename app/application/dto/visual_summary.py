from __future__ import annotations

import json
from typing import Any


SUPPORTED_VISUAL_BLOCK_TYPES = {
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
}

LEGACY_TYPE_MAP = {
    "key_points": "cards",
    "checklist": "steps",
    "warning": "callout",
    "quote": "callout",
}

ITEM_TITLE_KEYS = ("title", "term", "mistake", "name", "label")
ITEM_BODY_KEYS = (
    "text",
    "definition",
    "correction",
    "formula",
    "description",
    "content",
    "answer",
    "explanation",
    "value",
)
STRUCTURAL_KEYS = {
    "type",
    "items",
    "sections",
    "blocks",
    "nodes",
    "edges",
    "left",
    "right",
    "headers",
    "columns",
    "rows",
    "labels",
    "values",
    "chart_type",
    "unit",
}


def parse_visual_summary(raw: str | dict[str, Any] | None) -> dict[str, Any] | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        value = raw
    else:
        try:
            value = json.loads(raw or "{}")
        except json.JSONDecodeError:
            return None
    if not isinstance(value, dict):
        return None
    return normalize_visual_summary(value)


def dump_visual_summary(raw: str | dict[str, Any] | None) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str) and not raw.strip():
        return ""
    if isinstance(raw, dict) and not _has_declared_visual_content(raw):
        return ""
    parsed = parse_visual_summary(raw)
    if parsed is None:
        return str(raw or "")
    if not parsed["sections"] and parsed["title"] == "Resumo visual" and not parsed["subtitle"]:
        return ""
    return json.dumps(parsed, ensure_ascii=False, indent=2)


def normalize_visual_summary(data: dict[str, Any]) -> dict[str, Any]:
    title = _text(data.get("title"), "Resumo visual")
    subtitle = _text(data.get("subtitle"), "")
    sections = data.get("sections")
    if not isinstance(sections, list):
        sections = data.get("blocks") if isinstance(data.get("blocks"), list) else []

    normalized_sections = [
        normalize_visual_block(section)
        for section in sections
        if isinstance(section, dict)
    ]
    if not normalized_sections and (data.get("text") or data.get("content")):
        normalized_sections.append(
            normalize_visual_block(
                {
                    "type": "section",
                    "title": title,
                    "text": data.get("text") or data.get("content"),
                }
            )
        )

    return {
        "title": title,
        "subtitle": subtitle,
        "sections": normalized_sections,
    }


def normalize_visual_block(block: dict[str, Any]) -> dict[str, Any]:
    raw_type = _text(block.get("type"), "section").lower()
    block_type = LEGACY_TYPE_MAP.get(raw_type, raw_type)
    if block_type not in SUPPORTED_VISUAL_BLOCK_TYPES:
        block_type = "section"

    normalized = dict(block)
    normalized["type"] = block_type
    if not _text(normalized.get("title")):
        normalized["title"] = _default_title(block_type)
    normalized["text"] = _block_text(block)

    if block_type == "callout":
        normalized["variant"] = _callout_variant(block, raw_type)
        normalized["items"] = _items(block.get("items"))
    elif block_type == "cards":
        normalized["items"] = _items(block.get("items"))
    elif block_type == "comparison":
        normalized["items"] = _comparison_items(block)
    elif block_type in {"steps", "timeline", "mistakes"}:
        normalized["items"] = _items(block.get("items"))
    elif block_type == "tags":
        normalized["items"] = _string_items(block.get("items"))
    elif block_type == "flow":
        normalized["items"] = _flow_items(block)
    elif block_type == "table":
        normalized["headers"] = _headers(block)
        normalized["rows"] = _rows(block.get("rows"))
    elif block_type in {"formula", "definition", "example"}:
        normalized["items"] = _definition_items(block)
    elif block_type == "chart":
        normalized["chart_type"] = _chart_type(block.get("chart_type"))
        normalized["labels"] = _string_items(block.get("labels"))
        normalized["values"] = _numbers(block.get("values"))
    return normalized


def visual_summary_slides(data: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not data:
        return []
    slides: list[dict[str, Any]] = []
    title = _text(data.get("title"), "Resumo visual")
    subtitle = _text(data.get("subtitle"), "")
    sections = data.get("sections") if isinstance(data.get("sections"), list) else []

    has_explicit_hero = bool(sections and isinstance(sections[0], dict) and sections[0].get("type") == "hero")
    if not has_explicit_hero:
        slides.append(
            {
                "type": "hero",
                "title": title,
                "subtitle": subtitle,
                "text": "Revisao visual gerada para este bloco.",
            }
        )
    slides.extend(section for section in sections if isinstance(section, dict))
    return slides


def _text(value: object, fallback: str = "") -> str:
    text = str(value).strip() if value is not None else ""
    return text or fallback


def _has_declared_visual_content(data: dict[str, Any]) -> bool:
    if _text(data.get("title")) or _text(data.get("subtitle")):
        return True
    if _text(data.get("text")) or _text(data.get("content")):
        return True
    for key in ("sections", "blocks", "items", "nodes", "rows", "labels", "values"):
        value = data.get(key)
        if isinstance(value, list) and value:
            return True
    return any(key not in {"schema_version"} and value for key, value in data.items())


def _items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    items: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        normalized = _visual_item(item, index)
        if normalized["title"] or normalized["text"]:
            items.append(normalized)
    return items


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for index, item in enumerate(value, start=1):
        if isinstance(item, dict):
            normalized = _visual_item(item, index)
            text = normalized["title"] or normalized["text"]
            if text:
                items.append(text)
        elif item is not None:
            items.append(_text(item))
    return items


def _visual_item(value: object, index: int = 1) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"title": _text(value), "text": "", "number": str(index)}

    number = _text(value.get("step") or value.get("number"), str(index))
    title_key, title = _first_text(value, ITEM_TITLE_KEYS)
    body_values = [
        text
        for key in ITEM_BODY_KEYS
        if (text := _text(value.get(key)))
    ]
    body = "\n".join(body_values)

    if not title and body:
        title = body_values[0]
        body = "\n".join(body_values[1:])
    if not title:
        title = _first_generic_text(value, excluded=STRUCTURAL_KEYS | set(ITEM_BODY_KEYS))[1]
    if not body:
        body = _generic_body(value, excluded=STRUCTURAL_KEYS | {title_key, *ITEM_TITLE_KEYS})

    item: dict[str, Any] = {
        "title": title,
        "text": body,
        "number": number,
    }
    points = _string_items(value.get("items"))
    if points:
        item["points"] = points
    return item


def _definition_items(block: dict[str, Any]) -> list[dict[str, Any]]:
    items = _items(block.get("items"))
    if items:
        return items
    source = {
        key: value
        for key, value in block.items()
        if key not in STRUCTURAL_KEYS and key != "title"
    }
    item = _visual_item(source, 1)
    return [item] if item["title"] or item["text"] else []


def _comparison_items(block: dict[str, Any]) -> list[dict[str, Any]]:
    items = _items(block.get("items"))
    sides: list[dict[str, Any]] = []
    for key in ("left", "right"):
        side = block.get(key)
        if isinstance(side, dict):
            title = _text(side.get("title") or side.get("label") or key.title(), key.title())
            points = _string_items(side.get("items"))
            text = _text(side.get("text") or side.get("description") or side.get("content"))
            sides.append(
                {
                    "title": title,
                    "text": text,
                    "number": str(len(sides) + 1),
                    "points": points,
                }
            )
    return sides or items


def _flow_items(block: dict[str, Any]) -> list[str]:
    direct_items = _string_items(block.get("items"))
    if direct_items:
        return direct_items

    nodes = block.get("nodes")
    if not isinstance(nodes, list):
        return []
    node_ids: list[str] = []
    labels_by_id: dict[str, str] = {}
    for index, node in enumerate(nodes, start=1):
        if not isinstance(node, dict):
            label = _text(node)
            node_id = str(index)
        else:
            node_id = _text(node.get("id"), str(index))
            label = _text(node.get("label") or node.get("title") or node.get("name"), node_id)
        if node_id:
            node_ids.append(node_id)
            labels_by_id[node_id] = label

    edges = block.get("edges")
    if not isinstance(edges, list) or not edges:
        return [labels_by_id[node_id] for node_id in node_ids if labels_by_id.get(node_id)]

    outgoing: dict[str, str] = {}
    incoming: set[str] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source = _text(edge.get("from") or edge.get("source"))
        target = _text(edge.get("to") or edge.get("target"))
        if source and target and source not in outgoing:
            outgoing[source] = target
            incoming.add(target)

    start = next((node_id for node_id in node_ids if node_id not in incoming), node_ids[0] if node_ids else "")
    ordered: list[str] = []
    seen: set[str] = set()
    current = start
    while current and current not in seen and current in labels_by_id:
        ordered.append(current)
        seen.add(current)
        current = outgoing.get(current, "")
    ordered.extend(node_id for node_id in node_ids if node_id not in seen)
    return [labels_by_id[node_id] for node_id in ordered if labels_by_id.get(node_id)]


def _headers(block: dict[str, Any]) -> list[str]:
    headers = block.get("headers") if isinstance(block.get("headers"), list) else block.get("columns")
    return _string_items(headers)


def _rows(value: object) -> list[list[str]]:
    if not isinstance(value, list):
        return []
    rows: list[list[str]] = []
    for row in value:
        if isinstance(row, list):
            rows.append([_text(cell) for cell in row])
        elif isinstance(row, dict):
            rows.append([_text(cell) for cell in row.values()])
    return rows


def _block_text(block: dict[str, Any]) -> str:
    text = _text(block.get("text") or block.get("content") or block.get("description"))
    if text:
        return text
    return _generic_body(block, excluded=STRUCTURAL_KEYS | {"title", "subtitle", "variant"})


def _first_text(data: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, str]:
    for key in keys:
        text = _text(data.get(key))
        if text:
            return key, text
    return "", ""


def _first_generic_text(data: dict[str, Any], excluded: set[str]) -> tuple[str, str]:
    for key, value in data.items():
        if key in excluded:
            continue
        if isinstance(value, (str, int, float)) and _text(value):
            return key, _text(value)
    return "", ""


def _generic_body(data: dict[str, Any], excluded: set[str]) -> str:
    parts: list[str] = []
    for key, value in data.items():
        if key in excluded or value is None:
            continue
        if isinstance(value, (str, int, float)):
            text = _text(value)
            if text:
                parts.append(text)
        elif isinstance(value, list):
            values = _string_items(value)
            if values:
                parts.append("\n".join(values))
    return "\n".join(part for part in parts if part)


def _numbers(value: object) -> list[float]:
    if not isinstance(value, list):
        return []
    numbers: list[float] = []
    for item in value:
        try:
            numbers.append(float(item))
        except (TypeError, ValueError):
            continue
    return numbers


def _chart_type(value: object) -> str:
    chart_type = _text(value, "bar").lower()
    return chart_type if chart_type in {"bar", "horizontal_bar", "donut", "ring", "progress"} else "bar"


def _callout_variant(block: dict[str, Any], raw_type: str) -> str:
    variant = _text(block.get("variant"), raw_type).lower()
    if variant == "quote":
        return "info"
    if variant in {"info", "success", "warning", "danger", "tip", "example", "formula"}:
        return variant
    return "info"


def _default_title(block_type: str) -> str:
    return {
        "hero": "Ideia central",
        "section": "Secao",
        "cards": "Pontos importantes",
        "callout": "Destaque",
        "table": "Tabela",
        "comparison": "Comparacao",
        "steps": "Passos",
        "timeline": "Linha do tempo",
        "tags": "Tags",
        "formula": "Formula",
        "definition": "Definicao",
        "example": "Exemplo",
        "mistakes": "Erros comuns",
        "flow": "Fluxo",
        "chart": "Grafico",
    }.get(block_type, "Secao")
