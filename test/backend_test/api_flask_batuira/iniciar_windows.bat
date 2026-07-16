@echo off
if not exist venv\Scripts\python.exe (
  echo Execute configurar_windows.bat primeiro.
  pause
  exit /b 1
)
call venv\Scripts\activate
python app.py
pause
