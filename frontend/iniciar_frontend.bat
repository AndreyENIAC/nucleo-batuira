@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "VPY=%~dp0..\backend\venv\Scripts\python.exe"
set "RUNNER=%~dp0..\backend\executar_com_log.py"
set "ANALISADOR=%~dp0..\backend\analisar_erro.py"
set "LOGDIR=%~dp0..\backend\logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>&1
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss" 2^>nul') do set "STAMP=%%I"
if not defined STAMP set "STAMP=sem_data"
set "LOG=%LOGDIR%\frontend_%STAMP%.log"
set "ULTIMO_LOG=%LOGDIR%\ultimo_frontend.log"

if not exist "%VPY%" (
    echo.
    echo ERRO: o Python do ambiente virtual nao foi encontrado.
    echo Execute primeiro: ..\backend\configurar_windows.bat
    pause
    exit /b 1
)

if not exist "%RUNNER%" (
    echo ERRO: executar_com_log.py nao foi encontrado no Backend.
    echo Copie novamente os arquivos da correcao V3.
    pause
    exit /b 1
)

>"%LOG%" echo FRONTEND NUCLEO BATUIRA - %date% %time%
echo ============================================================
echo FRONTEND - NUCLEO BATUIRA
echo ============================================================
echo Endereco esperado: http://127.0.0.1:5500/login.html
echo Log: %LOG%
echo Para encerrar, pressione CTRL+C.
echo.

"%VPY%" "%RUNNER%" --log "%LOG%" --cwd "%CD%" -- "%VPY%" -u -m http.server 5500 --bind 127.0.0.1
set "CODIGO=!errorlevel!"
copy /y "%LOG%" "%ULTIMO_LOG%" >nul 2>&1

if not "!CODIGO!"=="0" (
    echo.
    echo ============================================================
    echo O FRONTEND FOI ENCERRADO COM ERRO !CODIGO!
    echo ============================================================
    echo Log completo:
    echo %LOG%
    echo.
    if exist "%ANALISADOR%" (
        "%VPY%" "%ANALISADOR%" "%LOG%"
    )
    start "" notepad "%LOG%"
) else (
    echo.
    echo O Frontend foi encerrado normalmente.
)
pause
exit /b !CODIGO!
