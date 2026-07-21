"""Atualiza um banco existente para a Etapa 3 sem apagar dados.

Execute uma vez:
    python migrar_etapa3_institucional.py
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "batuira.db"


def coluna_existe(conn, tabela, coluna):
    return any(linha[1] == coluna for linha in conn.execute(f"PRAGMA table_info({tabela})"))


def migrar():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        if not coluna_existe(conn, "eventos_agenda", "setor"):
            conn.execute(
                "ALTER TABLE eventos_agenda ADD COLUMN setor TEXT NOT NULL DEFAULT 'geral'"
            )

        conn.execute(
            """
            UPDATE eventos_agenda
            SET setor = CASE
                WHEN lower(tipo || ' ' || titulo) LIKE '%consulta%'
                  OR lower(tipo || ' ' || titulo) LIKE '%médic%'
                  OR lower(tipo || ' ' || titulo) LIKE '%medic%'
                  OR lower(tipo || ' ' || titulo) LIKE '%saúde%'
                  OR lower(tipo || ' ' || titulo) LIKE '%saude%'
                    THEN 'saude'
                WHEN lower(tipo || ' ' || titulo) LIKE '%finance%'
                  OR lower(tipo || ' ' || titulo) LIKE '%prestação%'
                  OR lower(tipo || ' ' || titulo) LIKE '%prestacao%'
                  OR lower(tipo || ' ' || titulo) LIKE '%doação%'
                  OR lower(tipo || ' ' || titulo) LIKE '%doacao%'
                  OR lower(tipo || ' ' || titulo) LIKE '%pagamento%'
                    THEN 'institucional'
                ELSE COALESCE(NULLIF(setor, ''), 'geral')
            END
            """
        )

        categoria_antiga = conn.execute(
            "SELECT id FROM categorias_financeiras "
            "WHERE tipo = 'despesa' AND nome = 'Outras despesas'"
        ).fetchone()
        categoria_nova = conn.execute(
            "SELECT id FROM categorias_financeiras "
            "WHERE tipo = 'despesa' AND nome = 'Outros'"
        ).fetchone()

        if categoria_antiga and categoria_nova:
            conn.execute(
                "UPDATE gastos SET categoria_id = ? WHERE categoria_id = ?",
                (categoria_nova[0], categoria_antiga[0]),
            )
            conn.execute(
                "DELETE FROM categorias_financeiras WHERE id = ?",
                (categoria_antiga[0],),
            )
        elif categoria_antiga:
            conn.execute(
                "UPDATE categorias_financeiras SET nome = 'Outros' WHERE id = ?",
                (categoria_antiga[0],),
            )
        elif not categoria_nova:
            conn.execute(
                "INSERT INTO categorias_financeiras (nome, tipo, ativo) "
                "VALUES ('Outros', 'despesa', 1)"
            )

        categorias_receita = [
            "Verba municipal",
            "Convênio público",
            "Doações",
            "Benefícios de acolhidos",
            "Outras receitas",
        ]
        for nome in categorias_receita:
            conn.execute(
                "INSERT OR IGNORE INTO categorias_financeiras (nome, tipo, ativo) "
                "VALUES (?, 'receita', 1)",
                (nome,),
            )

        conn.execute(
            "UPDATE perfis_acesso SET nome = 'Equipe Institucional', "
            "descricao = 'Acesso de edição à Gestão Institucional.' "
            "WHERE codigo = 'financial'"
        )
        conn.execute(
            "UPDATE perfis_acesso SET descricao = "
            "'Acesso somente para leitura a todos os módulos, exceto usuários.' "
            "WHERE codigo = 'staff'"
        )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_eventos_setor_inicio "
            "ON eventos_agenda(setor, inicio)"
        )
        conn.commit()

    print("Migração da Etapa 3 concluída sem apagar os dados.")


if __name__ == "__main__":
    migrar()
