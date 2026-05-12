from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def new_id() -> str:
    return str(uuid4())


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}
