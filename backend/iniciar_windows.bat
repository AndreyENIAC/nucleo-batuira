@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

if not exist "logs" mkdir "logs" >nul 2>&1
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss" 2^>nul') do set "STAMP=%%I"
if not defined STAMP set "STAMP=sem_data"
set "LOG=%CD%\logs\backend_%STAMP%.log"
set "ULTIMO_LOG=%CD%\logs\ultimo_backend.log"
set "VPY=%CD%\venv\Scripts\python.exe"

if not exist "%VPY%" (
    echo.
    echo ERRO: o ambiente virtual do Backend nao esta pronto.
    echo Execute primeiro: configurar_windows.bat
    echo Depois consulte: logs\ultima_configuracao.log
    pause
    exit /b 1
)

if not exist "app.py" (
    echo ERRO: app.py nao foi encontrado na pasta do Backend.
    pause
    exit /b 1
)

>"%LOG%" echo BACKEND NUCLEO BATUIRA - %date% %time%
echo ============================================================
echo BACKEND FLASK - NUCLEO BATUIRA
echo ============================================================
echo Endereco esperado: http://127.0.0.1:5000
echo Log: %LOG%
echo Para encerrar, pressione CTRL+C.
echo.

set "PYTHONUNBUFFERED=1"
where powershell >nul 2>&1
if errorlevel 1 (
    "%VPY%" "app.py"
    set "CODIGO=!errorlevel!"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "& '%VPY%' 'app.py' 2^>^&1 | Tee-Object -FilePath '%LOG%' -Append; exit $LASTEXITCODE"
    set "CODIGO=!errorlevel!"
)
copy /y "%LOG%" "%ULTIMO_LOG%" >nul 2>&1

if not "%CODIGO%"=="0" (
    echo.
    echo ============================================================
    echo O BACKEND FOI ENCERRADO COM ERRO %CODIGO%
    echo ============================================================
    echo Consulte o arquivo:
    echo %LOG%
    start "" notepad "%LOG%"
) else (
    echo.
    echo O Backend foi encerrado.
)
pause
exit /b %CODIGO%
