from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable

from flask import current_app, g


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        database_path = Path(current_app.config["DATABASE_PATH"])
        database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        g.db = connection
    return g.db


def close_db(_: BaseException | None = None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def fetch_one(query: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
    row = get_db().execute(query, tuple(params)).fetchone()
    return dict(row) if row is not None else None


def fetch_all(query: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    rows = get_db().execute(query, tuple(params)).fetchall()
    return [dict(row) for row in rows]


def execute(query: str, params: Iterable[Any] = ()) -> int:
    cursor = get_db().execute(query, tuple(params))
    return int(cursor.lastrowid or 0)


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
