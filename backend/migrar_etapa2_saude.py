"""Migração segura da Etapa 2.

Adiciona a referência opcional entre alertas e a nota clínica que os originou.
Não apaga tabelas nem cadastros existentes.
"""

from pathlib import Path
import sqlite3

from database import DB_PATH


def colunas(conn, tabela):
    return {linha[1] for linha in conn.execute(f"PRAGMA table_info({tabela})")}


def migrar():
    conn = sqlite3.connect(DB_PATH)
    try:
        existentes = colunas(conn, "alertas")
        if "origem_tipo" not in existentes:
            conn.execute("ALTER TABLE alertas ADD COLUMN origem_tipo TEXT")
        if "origem_id" not in existentes:
            conn.execute("ALTER TABLE alertas ADD COLUMN origem_id INTEGER")

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_alertas_origem ON alertas(origem_tipo, origem_id)"
        )

        # Registros antigos de documento podem ter sido copiados sem seus arquivos físicos.
        # Mantemos os metadados, mas marcamos como indisponíveis para não simular um download válido.
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

        conn.commit()
        print("Migração da Etapa 2 aplicada com sucesso.")
    finally:
        conn.close()


if __name__ == "__main__":
    migrar()
