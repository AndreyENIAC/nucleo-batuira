"""Atualiza o banco existente sem apagar os dados.

Este arquivo reúne as atualizações que antes estavam separadas por etapas.
Ele pode ser executado mais de uma vez com segurança.
"""

from pathlib import Path
import sqlite3

from database import DB_PATH


def colunas_da_tabela(conn: sqlite3.Connection, tabela: str) -> set[str]:
    return {linha[1] for linha in conn.execute(f"PRAGMA table_info({tabela})")}


def atualizar_autenticacao(conn: sqlite3.Connection) -> None:
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


def atualizar_saude(conn: sqlite3.Connection) -> None:
    existentes = colunas_da_tabela(conn, "alertas")
    if "origem_tipo" not in existentes:
        conn.execute("ALTER TABLE alertas ADD COLUMN origem_tipo TEXT")
    if "origem_id" not in existentes:
        conn.execute("ALTER TABLE alertas ADD COLUMN origem_id INTEGER")

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_alertas_origem "
        "ON alertas(origem_tipo, origem_id)"
    )

    pasta_uploads = Path(DB_PATH).parent / "uploads"
    documentos = conn.execute(
        "SELECT id, caminho_arquivo FROM documentos WHERE status = 'ativo'"
    ).fetchall()
    for documento_id, caminho_arquivo in documentos:
        if not (pasta_uploads / caminho_arquivo).is_file():
            conn.execute(
                "UPDATE documentos SET status = 'indisponivel' WHERE id = ?",
                (documento_id,),
            )


def atualizar_institucional(conn: sqlite3.Connection) -> None:
    if "setor" not in colunas_da_tabela(conn, "eventos_agenda"):
        conn.execute(
            "ALTER TABLE eventos_agenda "
            "ADD COLUMN setor TEXT NOT NULL DEFAULT 'geral'"
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


def atualizar_banco() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        atualizar_autenticacao(conn)
        atualizar_saude(conn)
        atualizar_institucional(conn)
        conn.commit()

    print("Banco atualizado com sucesso, sem apagar os dados.")


if __name__ == "__main__":
    atualizar_banco()
