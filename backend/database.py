"""Funções simples para acessar o banco SQLite."""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "batuira.db"


def get_connection():
    """Abre uma conexão e permite acessar as colunas pelo nome."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row):
    """Converte uma linha do SQLite em dicionário."""
    return dict(row) if row is not None else None


def rows_to_list(rows):
    """Converte várias linhas do SQLite em lista de dicionários."""
    return [dict(row) for row in rows]
