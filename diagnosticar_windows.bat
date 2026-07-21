@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist "backend\logs" mkdir "backend\logs" >nul 2>&1
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss" 2^>nul') do set "STAMP=%%I"
if not defined STAMP set "STAMP=sem_data"
set "LOG=%CD%\backend\logs\diagnostico_%STAMP%.txt"
set "VPY=%CD%\backend\venv\Scripts\python.exe"

>"%LOG%" echo ============================================================
>>"%LOG%" echo DIAGNOSTICO DO PROJETO NUCLEO BATUIRA
>>"%LOG%" echo Data: %date% %time%
>>"%LOG%" echo Pasta: %CD%
>>"%LOG%" echo ============================================================

echo Criando diagnostico. Nenhum dado sera apagado ou alterado...

>>"%LOG%" echo.
>>"%LOG%" echo [1] WINDOWS
ver >>"%LOG%" 2>&1
whoami >>"%LOG%" 2>&1

>>"%LOG%" echo.
>>"%LOG%" echo [2] ARQUIVOS PRINCIPAIS
for %%F in ("backend\app.py" "backend\database.py" "backend\requirements.txt" "backend\batuira.db" "frontend\login.html") do (
    if exist %%F (
        >>"%LOG%" echo OK: %%~F
    ) else (
        >>"%LOG%" echo FALTANDO: %%~F
    )
)

>>"%LOG%" echo.
>>"%LOG%" echo [3] PYTHON DO WINDOWS
where py >>"%LOG%" 2>&1
py -3 --version >>"%LOG%" 2>&1
where python >>"%LOG%" 2>&1
python --version >>"%LOG%" 2>&1
where python3 >>"%LOG%" 2>&1
python3 --version >>"%LOG%" 2>&1

>>"%LOG%" echo.
>>"%LOG%" echo [4] AMBIENTE VIRTUAL
if exist "%VPY%" (
    >>"%LOG%" echo OK: %VPY%
    "%VPY%" --version >>"%LOG%" 2>&1
    "%VPY%" -m pip --version >>"%LOG%" 2>&1
    "%VPY%" -c "import flask, flask_cors, flask_jwt_extended, werkzeug; print('OK: dependencias principais importadas')" >>"%LOG%" 2>&1
) else (
    >>"%LOG%" echo ERRO: ambiente virtual ausente ou incompleto.
)

>>"%LOG%" echo.
>>"%LOG%" echo [5] BANCO SQLITE
if exist "backend\batuira.db" (
    for %%S in ("backend\batuira.db") do >>"%LOG%" echo Tamanho do banco: %%~zS bytes
    if exist "%VPY%" (
        pushd "backend"
        "%VPY%" -c "import sqlite3; c=sqlite3.connect(r'batuira.db'); print('Integridade:', c.execute('PRAGMA integrity_check').fetchone()[0]); print('Tabelas:', len(c.execute('SELECT name FROM sqlite_master WHERE type=?', ('table',)).fetchall())); c.close()" >>"%LOG%" 2>&1
        popd
    )
) else (
    >>"%LOG%" echo ERRO: batuira.db nao foi encontrado.
)

>>"%LOG%" echo.
>>"%LOG%" echo [6] SINTAXE E CARREGAMENTO DO FLASK
if exist "%VPY%" (
    pushd "backend"
    "%VPY%" -m py_compile "app.py" "database.py" >>"%LOG%" 2>&1
    "%VPY%" -c "from app import app; print('OK: Flask carregado -', app.name)" >>"%LOG%" 2>&1
    popd
) else (
    >>"%LOG%" echo Teste ignorado: ambiente virtual ausente.
)

>>"%LOG%" echo.
>>"%LOG%" echo [7] PORTAS
>>"%LOG%" echo Porta 5000:
netstat -ano | findstr ":5000" >>"%LOG%" 2>&1
>>"%LOG%" echo Porta 5500:
netstat -ano | findstr ":5500" >>"%LOG%" 2>&1

>>"%LOG%" echo.
>>"%LOG%" echo [8] TESTE DOS ENDERECOS, SE OS SERVIDORES ESTIVEREM ABERTOS
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r=Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:5000/' -TimeoutSec 2; 'Backend HTTP: ' + $r.StatusCode } catch { 'Backend HTTP: sem resposta - ' + $_.Exception.Message }" >>"%LOG%" 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r=Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:5500/login.html' -TimeoutSec 2; 'Frontend HTTP: ' + $r.StatusCode } catch { 'Frontend HTTP: sem resposta - ' + $_.Exception.Message }" >>"%LOG%" 2>&1

>>"%LOG%" echo.
>>"%LOG%" echo [9] ULTIMOS LOGS DISPONIVEIS
if exist "backend\logs" dir /b /o-d "backend\logs" >>"%LOG%" 2>&1

>>"%LOG%" echo.
>>"%LOG%" echo ============================================================
>>"%LOG%" echo FIM DO DIAGNOSTICO
>>"%LOG%" echo ============================================================

echo.
echo Diagnostico concluido:
echo %LOG%
echo.
echo O arquivo sera aberto no Bloco de Notas.
start "" notepad "%LOG%"
pause
exit /b 0
