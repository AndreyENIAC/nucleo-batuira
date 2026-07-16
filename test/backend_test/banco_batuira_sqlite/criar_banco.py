"""Cria do zero o banco SQLite do Núcleo Batuíra.

Uso:
    python criar_banco.py

O script recria o arquivo batuira.db na mesma pasta, aplica o schema,
insere os dados básicos e cria o usuário inicial:
    usuário: admin
    senha: admin123

No primeiro acesso, a senha deve ser alterada.
"""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "batuira.db"
SCHEMA_PATH = BASE_DIR / "schema_batuira.sql"
SEED_PATH = BASE_DIR / "seed_batuira.sql"


def gerar_hash_werkzeug_pbkdf2(senha: str, iteracoes: int = 600_000) -> str:
    """Gera hash compatível com werkzeug.security.check_password_hash."""
    alfabeto = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    salt = "".join(secrets.choice(alfabeto) for _ in range(16))
    metodo = f"pbkdf2:sha256:{iteracoes}"
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt.encode("utf-8"),
        iteracoes,
    ).hex()
    return f"{metodo}${salt}${digest}"


def criar_banco() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    seed = SEED_PATH.read_text(encoding="utf-8")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(schema)
        conn.executescript(seed)

        perfil_admin_id = conn.execute(
            "SELECT id FROM perfis_acesso WHERE codigo = 'admin'"
        ).fetchone()[0]

        conn.execute(
            """
            INSERT INTO usuarios (
                perfil_id, nome, username, email, senha_hash,
                profissao, primeiro_acesso, ativo
            ) VALUES (?, ?, ?, ?, ?, ?, 1, 1)
            """,
            (
                perfil_admin_id,
                "Administrador do Sistema",
                "admin",
                "admin@nucleobatuira.local",
                gerar_hash_werkzeug_pbkdf2("admin123"),
                "Administrador",
            ),
        )
        conn.commit()

        integridade = conn.execute("PRAGMA integrity_check").fetchone()[0]
        chaves_invalidas = conn.execute("PRAGMA foreign_key_check").fetchall()

    if integridade != "ok" or chaves_invalidas:
        raise RuntimeError(
            f"Falha na validação: integrity_check={integridade!r}, "
            f"foreign_key_check={chaves_invalidas!r}"
        )

    print(f"Banco criado com sucesso: {DB_PATH}")
    print("Usuário inicial: admin")
    print("Senha inicial: admin123")


if __name__ == "__main__":
    criar_banco()
