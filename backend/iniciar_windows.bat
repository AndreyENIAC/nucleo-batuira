@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

if not exist "logs" mkdir "logs" >nul 2>&1
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss" 2^>nul') do set "STAMP=%%I"
if not defined STAMP set "STAMP=sem_data"
set "LOG=%CD%\logs\backend_%STAMP%.log"
set "ULTIMO_LOG=%CD%\logs\ultimo_backend.log"
set "VPY=%CD%\venv\Scripts\python.exe"
set "RUNNER=%CD%\executar_com_log.py"
set "ANALISADOR=%CD%\analisar_erro.py"

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

if not exist "%RUNNER%" (
    echo ERRO: executar_com_log.py nao foi encontrado.
    echo Copie novamente os arquivos da correcao V3.
    pause
    exit /b 1
)

if exist "atualizar_banco.py" (
    echo Verificando atualizacoes do banco...
    "%VPY%" "atualizar_banco.py"
    if errorlevel 1 (
        echo ERRO: nao foi possivel atualizar o banco antes de iniciar.
        echo Execute backend\configurar_windows.bat e consulte o log.
        pause
        exit /b 1
    )
)

>"%LOG%" echo BACKEND NUCLEO BATUIRA - %date% %time%
echo ============================================================
echo BACKEND FLASK - NUCLEO BATUIRA
echo ============================================================
echo Endereco esperado: http://127.0.0.1:5000
echo Log: %LOG%
echo Para encerrar, pressione CTRL+C.
echo.

"%VPY%" "%RUNNER%" --log "%LOG%" --cwd "%CD%" -- "%VPY%" -u app.py
set "CODIGO=!errorlevel!"
copy /y "%LOG%" "%ULTIMO_LOG%" >nul 2>&1

if not "!CODIGO!"=="0" (
    echo.
    echo ============================================================
    echo O BACKEND FOI ENCERRADO COM ERRO !CODIGO!
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
    echo O Backend foi encerrado normalmente.
)
pause
exit /b !CODIGO!
