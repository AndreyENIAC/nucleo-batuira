"""Atualiza o banco existente para a Etapa 1 sem apagar os dados.

Execute uma única vez:
    python migrar_etapa1_autenticacao.py
"""

import sqlite3
from database import DB_PATH


def migrar():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS solicitacoes_recuperacao_senha (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pendente'
                    CHECK (status IN ('pendente', 'resolvida', 'cancelada')),
                solicitado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                resolvido_por INTEGER,
                resolvido_em TEXT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                    ON UPDATE CASCADE ON DELETE CASCADE,
                FOREIGN KEY (resolvido_por) REFERENCES usuarios(id)
                    ON UPDATE CASCADE ON DELETE SET NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_solicitacoes_recuperacao_usuario
            ON solicitacoes_recuperacao_senha(usuario_id, status)
            """
        )

        # A conta inicial admin/admin123 precisa escolher uma senha própria.
        conn.execute(
            "UPDATE usuarios SET primeiro_acesso = 1 WHERE username = 'admin'"
        )
        conn.commit()

    print("Migração concluída. O administrador deverá trocar a senha no próximo login.")


if __name__ == "__main__":
    migrar()
