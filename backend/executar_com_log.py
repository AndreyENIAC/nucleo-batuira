from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def imprimir_e_gravar(texto: str, arquivo) -> None:
    sys.stdout.write(texto)
    sys.stdout.flush()
    arquivo.write(texto)
    arquivo.flush()


def encerrar_arvore(processo: subprocess.Popen[str]) -> None:
    if processo.poll() is not None:
        return

    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(processo.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            processo.terminate()
            processo.wait(timeout=5)
    except Exception:
        try:
            processo.kill()
        except Exception:
            pass


def executar(comando: Sequence[str], pasta: Path, log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)

    ambiente = os.environ.copy()
    ambiente["PYTHONUNBUFFERED"] = "1"
    ambiente["PYTHONUTF8"] = "1"

    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    processo: subprocess.Popen[str] | None = None

    with log_path.open("a", encoding="utf-8", errors="replace", buffering=1) as log:
        imprimir_e_gravar("\n", log)
        imprimir_e_gravar("Comando: " + subprocess.list2cmdline(list(comando)) + "\n", log)
        imprimir_e_gravar("Pasta: " + str(pasta) + "\n\n", log)

        try:
            processo = subprocess.Popen(
                list(comando),
                cwd=str(pasta),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=ambiente,
                creationflags=creationflags,
            )

            assert processo.stdout is not None
            for linha in processo.stdout:
                imprimir_e_gravar(linha, log)

            return int(processo.wait())

        except KeyboardInterrupt:
            mensagem = "\nEncerramento solicitado pelo usuario (CTRL+C).\n"
            imprimir_e_gravar(mensagem, log)
            if processo is not None:
                encerrar_arvore(processo)
            return 0

        except FileNotFoundError as erro:
            imprimir_e_gravar(f"\nERRO: arquivo ou comando nao encontrado: {erro}\n", log)
            if processo is not None:
                encerrar_arvore(processo)
            return 2

        except Exception as erro:
            imprimir_e_gravar(
                f"\nERRO no executor: {type(erro).__name__}: {erro}\n", log
            )
            if processo is not None:
                encerrar_arvore(processo)
            return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Executa um comando, mostra a saida no terminal e grava um log."
    )
    parser.add_argument("--log", required=True, help="Caminho do arquivo de log.")
    parser.add_argument("--cwd", required=True, help="Pasta de execucao do comando.")
    parser.add_argument("comando", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    comando = list(args.comando)
    if comando and comando[0] == "--":
        comando = comando[1:]

    if not comando:
        print("ERRO: nenhum comando foi informado ao executor.")
        return 2

    return executar(comando, Path(args.cwd), Path(args.log))


if __name__ == "__main__":
    raise SystemExit(main())
