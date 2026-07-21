from __future__ import annotations

import re
import sys
from pathlib import Path


def diagnosticar(texto: str) -> list[str]:
    regras = [
        (r"Address already in use|WinError 10048|Only one usage of each socket", "A porta 5000 ja esta sendo usada por outro programa ou por outro Flask."),
        (r"ModuleNotFoundError: No module named ['\"]([^'\"]+)", "Uma biblioteca Python necessaria nao foi instalada no ambiente virtual."),
        (r"no such table", "O banco esta sem uma tabela esperada. Execute configurar_windows.bat para aplicar as migracoes."),
        (r"no such column", "O banco esta sem uma coluna esperada. Execute configurar_windows.bat para aplicar as migracoes."),
        (r"database is locked", "O SQLite esta bloqueado. Feche DB Browser, outro Backend e qualquer programa usando batuira.db."),
        (r"UNIQUE constraint failed", "Foi enviado um valor que precisa ser unico e ja existe no banco, como username ou CPF."),
        (r"SyntaxError|IndentationError|TabError", "Existe um erro de sintaxe ou de recuo em algum arquivo Python."),
        (r"PermissionError|Access is denied|Acesso negado", "O Windows negou acesso a um arquivo ou pasta. Verifique permissoes e antivirus."),
        (r"FileNotFoundError|The system cannot find the file", "Um arquivo ou caminho necessario nao foi encontrado."),
        (r"ImportError", "Uma importacao Python falhou. Verifique requirements.txt e o ambiente virtual."),
        (r"sqlite3\.OperationalError", "O SQLite encontrou um erro operacional. Confira a mensagem detalhada no final do log."),
    ]

    encontrados: list[str] = []
    for padrao, mensagem in regras:
        if re.search(padrao, texto, flags=re.IGNORECASE):
            encontrados.append(mensagem)
    return encontrados


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python analisar_erro.py CAMINHO_DO_LOG")
        return 2

    caminho = Path(sys.argv[1])
    if not caminho.exists():
        print(f"O arquivo de log nao foi encontrado: {caminho}")
        return 2

    texto = caminho.read_text(encoding="utf-8", errors="replace")
    linhas = texto.splitlines()
    achados = diagnosticar(texto)

    print("\nDIAGNOSTICO AUTOMATICO")
    print("-" * 60)
    if achados:
        for item in achados:
            print(f"- {item}")
    else:
        print("- O erro nao correspondeu aos casos mais comuns.")
        print("- Confira as ultimas linhas abaixo ou envie o arquivo completo.")

    print("\nULTIMAS LINHAS DO LOG")
    print("-" * 60)
    for linha in linhas[-45:]:
        print(linha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
