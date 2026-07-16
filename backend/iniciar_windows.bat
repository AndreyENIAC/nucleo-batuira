@echo off
if not exist venv (
  echo O ambiente virtual ainda nao existe.
  echo Execute primeiro: configurar_windows.bat
  pause
  exit /b
)
call venv\Scripts\activate
python app.py
pause
