@echo off
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python criar_banco.py
echo.
echo Configuracao concluida.
echo Agora execute iniciar_windows.bat
pause
