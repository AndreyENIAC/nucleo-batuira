@echo off
if not exist backend\venv (
  echo O ambiente virtual do Backend ainda nao existe.
  echo Execute primeiro: backend\configurar_windows.bat
  pause
  exit /b
)
start "Backend Flask" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate && python app.py"
start "Frontend" cmd /k "cd /d %~dp0frontend && python -m http.server 5500"
timeout /t 3 >nul
start http://127.0.0.1:5500/login.html
