@echo off
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if exist batuira.db (
  echo Banco existente encontrado. Aplicando atualizacao sem apagar os dados...
  python migrar_etapa1_autenticacao.py
  python migrar_etapa2_saude.py
  python migrar_etapa3_institucional.py
) else (
  echo Criando banco de demonstracao...
  python criar_banco.py
)

echo.
echo Configuracao concluida.
echo Agora execute iniciar_windows.bat
pause
