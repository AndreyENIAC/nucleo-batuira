@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist "logs" mkdir "logs" >nul 2>&1
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss" 2^>nul') do set "STAMP=%%I"
if not defined STAMP set "STAMP=sem_data"
set "LOG=%CD%\logs\configuracao_%STAMP%.log"
set "ULTIMO_LOG=%CD%\logs\ultima_configuracao.log"

>"%LOG%" echo ============================================================
>>"%LOG%" echo CONFIGURACAO DO BACKEND - NUCLEO BATUIRA
>>"%LOG%" echo Data: %date% %time%
>>"%LOG%" echo Pasta: %CD%
>>"%LOG%" echo ============================================================

echo.
echo ============================================================
echo CONFIGURACAO DO BACKEND - NUCLEO BATUIRA
echo ============================================================
echo Um relatorio sera salvo em:
echo %LOG%
echo.

echo [1/8] Procurando uma instalacao valida do Python...
call :detectar_python
if errorlevel 1 (
    set "ERRO_MSG=Python nao foi encontrado ou nao consegue ser executado."
    goto :FALHA
)
for /f "tokens=2" %%V in ('%PY_CMD% --version 2^>^&1') do set "PY_VERSION=%%V"
echo Python encontrado: %PY_VERSION%
>>"%LOG%" echo Python escolhido: %PY_CMD% - versao %PY_VERSION%

echo.
echo [2/8] Verificando o ambiente virtual...
if exist "venv" if not exist "venv\Scripts\python.exe" (
    echo Ambiente virtual incompleto encontrado. Ele sera recriado.
    >>"%LOG%" echo Ambiente virtual incompleto. Removendo a pasta venv.
    rmdir /s /q "venv" >>"%LOG%" 2>&1
    if exist "venv" (
        set "ERRO_MSG=Nao foi possivel remover a pasta venv incompleta. Feche programas que estejam usando essa pasta."
        goto :FALHA
    )
)

if not exist "venv\Scripts\python.exe" (
    echo Criando o ambiente virtual...
    >>"%LOG%" echo Executando: %PY_CMD% -m venv venv
    %PY_CMD% -m venv "venv" >>"%LOG%" 2>&1
    if errorlevel 1 (
        set "ERRO_MSG=Nao foi possivel criar o ambiente virtual."
        goto :FALHA
    )
) else (
    echo Ambiente virtual ja existe e sera reutilizado.
    >>"%LOG%" echo Ambiente virtual existente reutilizado.
)
set "VPY=%CD%\venv\Scripts\python.exe"

if not exist "%VPY%" (
    set "ERRO_MSG=O Python do ambiente virtual nao foi encontrado."
    goto :FALHA
)

echo.
echo [3/8] Verificando o instalador de pacotes pip...
"%VPY%" -m pip --version >>"%LOG%" 2>&1
if errorlevel 1 (
    echo O pip nao foi encontrado no ambiente virtual. Tentando corrigir...
    "%VPY%" -m ensurepip --upgrade >>"%LOG%" 2>&1
    if errorlevel 1 (
        set "ERRO_MSG=Nao foi possivel instalar ou reparar o pip."
        goto :FALHA
    )
)

echo.
echo [4/8] Atualizando o pip...
"%VPY%" -m pip install --upgrade pip >>"%LOG%" 2>&1
if errorlevel 1 (
    echo AVISO: nao foi possivel atualizar o pip. A configuracao continuara.
    >>"%LOG%" echo AVISO: atualizacao do pip falhou, mas a configuracao continuou.
)

echo.
echo [5/8] Instalando as bibliotecas do projeto...
if not exist "requirements.txt" (
    set "ERRO_MSG=O arquivo requirements.txt nao foi encontrado."
    goto :FALHA
)
"%VPY%" -m pip install -r "requirements.txt" >>"%LOG%" 2>&1
if errorlevel 1 (
    set "ERRO_MSG=Falha ao instalar as bibliotecas do requirements.txt. Verifique a internet e o log."
    goto :FALHA
)

"%VPY%" -c "import flask, flask_cors, flask_jwt_extended, werkzeug; print('Dependencias importadas com sucesso.')" >>"%LOG%" 2>&1
if errorlevel 1 (
    set "ERRO_MSG=As bibliotecas foram instaladas, mas alguma delas nao pode ser importada."
    goto :FALHA
)

echo.
echo [6/8] Preparando o banco de dados...
if exist "batuira.db" (
    echo Banco existente encontrado. Aplicando atualizacoes sem apagar os dados...
    call :executar_python "atualizar_banco.py" "Atualizacao do banco"
    if errorlevel 1 goto :FALHA
) else (
    echo Nenhum banco existente foi encontrado. Criando o banco de demonstracao...
    call :executar_python "criar_banco.py" "Criacao do banco"
    if errorlevel 1 goto :FALHA
)

if not exist "batuira.db" (
    set "ERRO_MSG=O processo terminou, mas o arquivo batuira.db nao foi encontrado."
    goto :FALHA
)

echo.
echo [7/8] Verificando a integridade do banco...
"%VPY%" -c "import sqlite3; c=sqlite3.connect(r'batuira.db'); r=c.execute('PRAGMA integrity_check').fetchone()[0]; print('Integridade do banco:', r); c.close(); raise SystemExit(0 if r == 'ok' else 1)" >>"%LOG%" 2>&1
if errorlevel 1 (
    set "ERRO_MSG=O SQLite informou um problema de integridade no banco."
    goto :FALHA
)

echo.
echo [8/8] Verificando os arquivos Python e a aplicacao Flask...
"%VPY%" -m py_compile "app.py" "database.py" "criar_banco.py" "atualizar_banco.py" "resetar_admin.py" >>"%LOG%" 2>&1
if errorlevel 1 (
    set "ERRO_MSG=Foi encontrado um erro de sintaxe em um arquivo Python."
    goto :FALHA
)
"%VPY%" -c "from app import app; print('Aplicacao Flask carregada:', app.name)" >>"%LOG%" 2>&1
if errorlevel 1 (
    set "ERRO_MSG=O Flask nao conseguiu carregar o arquivo app.py."
    goto :FALHA
)

echo.
echo ============================================================
echo CONFIGURACAO CONCLUIDA COM SUCESSO
echo ============================================================
echo Python: %PY_VERSION%
echo Banco: verificado
echo Bibliotecas: instaladas
echo.
echo Agora execute o arquivo iniciar_projeto.bat na pasta principal.
echo Log completo: %LOG%
>>"%LOG%" echo CONFIGURACAO CONCLUIDA COM SUCESSO.
copy /y "%LOG%" "%ULTIMO_LOG%" >nul 2>&1
start "" notepad "%LOG%"
pause
exit /b 0

:detectar_python
set "PY_CMD="
py -3 --version >>"%LOG%" 2>&1
if not errorlevel 1 set "PY_CMD=py -3"
if defined PY_CMD exit /b 0

python --version >>"%LOG%" 2>&1
if not errorlevel 1 set "PY_CMD=python"
if defined PY_CMD exit /b 0

python3 --version >>"%LOG%" 2>&1
if not errorlevel 1 set "PY_CMD=python3"
if defined PY_CMD exit /b 0

exit /b 1

:executar_python
set "ARQUIVO=%~1"
set "ETAPA=%~2"
if not exist "%ARQUIVO%" (
    set "ERRO_MSG=Arquivo necessario nao encontrado: %ARQUIVO%"
    exit /b 1
)
echo Executando: %ETAPA%...
>>"%LOG%" echo.
>>"%LOG%" echo Executando: %ETAPA% - %ARQUIVO%
"%VPY%" "%ARQUIVO%" >>"%LOG%" 2>&1
if errorlevel 1 (
    set "ERRO_MSG=Falha durante: %ETAPA%."
    exit /b 1
)
exit /b 0

:FALHA
if not defined ERRO_MSG set "ERRO_MSG=Ocorreu um erro desconhecido durante a configuracao."
>>"%LOG%" echo.
>>"%LOG%" echo ERRO: %ERRO_MSG%
copy /y "%LOG%" "%ULTIMO_LOG%" >nul 2>&1

echo.
echo ============================================================
echo ERRO NA CONFIGURACAO
echo ============================================================
echo %ERRO_MSG%
echo.
echo O projeto NAO foi configurado por completo.
echo Leia as ultimas linhas abaixo e abra o log para ver os detalhes:
echo %LOG%
echo.
call :mostrar_final_log
start "" notepad "%LOG%"
echo.
echo Dica: execute tambem o arquivo diagnosticar_windows.bat da pasta principal.
pause
exit /b 1

:mostrar_final_log
where powershell >nul 2>&1
if errorlevel 1 (
    type "%LOG%"
) else (
    powershell -NoProfile -Command "Get-Content -LiteralPath '%LOG%' -Tail 45"
)
exit /b 0
