from werkzeug.security import generate_password_hash

from database import get_connection


def main():
    nova_senha = "admin123"

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE usuarios
            SET senha_hash = ?,
                primeiro_acesso = 1,
                ativo = 1,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE username = ?
            """,
            (
                generate_password_hash(nova_senha),
                "admin",
            ),
        )
        conn.commit()

    if cursor.rowcount == 0:
        print("ERRO: O usuário admin não foi encontrado.")
        return

    print("Senha do administrador redefinida com sucesso.")
    print("Usuário: admin")
    print("Senha temporária: admin123")
    print("Primeiro acesso ativado novamente.")


if __name__ == "__main__":
    main()