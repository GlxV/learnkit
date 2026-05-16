from __future__ import annotations

import sqlite3
from pathlib import Path


def connect_sqlite(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(Path(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

