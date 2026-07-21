@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "VPY=%CD%\backend\venv\Scripts\python.exe"
if not exist "%VPY%" (
    echo.
    echo ============================================================
    echo PROJETO AINDA NAO CONFIGURADO
    echo ============================================================
    echo Execute primeiro:
    echo backend\configurar_windows.bat
    echo.
    echo Em caso de erro, execute:
    echo diagnosticar_windows.bat
    pause
    exit /b 1
)

call :verificar_porta 5000
if errorlevel 1 (
    echo.
    echo ERRO: a porta 5000 ja esta sendo usada por outro programa.
    echo Feche outra instancia do Backend ou descubra o processo com:
    echo netstat -ano ^| findstr :5000
    pause
    exit /b 1
)

call :verificar_porta 5500
if errorlevel 1 (
    echo.
    echo ERRO: a porta 5500 ja esta sendo usada por outro programa.
    echo Feche outra instancia do Frontend ou descubra o processo com:
    echo netstat -ano ^| findstr :5500
    pause
    exit /b 1
)

echo Iniciando o Backend e o Frontend...
start "Backend Flask - Nucleo Batuira" "%ComSpec%" /k call "%CD%\backend\iniciar_windows.bat"
start "Frontend - Nucleo Batuira" "%ComSpec%" /k call "%CD%\frontend\iniciar_frontend.bat"

echo Aguardando o Backend responder...
set /a TENTATIVAS=0
:AGUARDAR_BACKEND
call :testar_url "http://127.0.0.1:5000/"
if not errorlevel 1 goto :BACKEND_OK
set /a TENTATIVAS+=1
if !TENTATIVAS! GEQ 20 goto :ERRO_BACKEND
timeout /t 1 /nobreak >nul
goto :AGUARDAR_BACKEND

:BACKEND_OK
echo Backend respondeu corretamente.
echo Aguardando o Frontend responder...
set /a TENTATIVAS=0
:AGUARDAR_FRONTEND
call :testar_url "http://127.0.0.1:5500/login.html"
if not errorlevel 1 goto :TUDO_OK
set /a TENTATIVAS+=1
if !TENTATIVAS! GEQ 20 goto :ERRO_FRONTEND
timeout /t 1 /nobreak >nul
goto :AGUARDAR_FRONTEND

:TUDO_OK
echo Frontend respondeu corretamente.
echo Abrindo o sistema no navegador...
start "" "http://127.0.0.1:5500/login.html"
exit /b 0

:ERRO_BACKEND
echo.
echo ============================================================
echo O BACKEND NAO RESPONDEU NA PORTA 5000
echo ============================================================
echo Confira a janela "Backend Flask - Nucleo Batuira".
echo Log: backend\logs\ultimo_backend.log
echo Execute diagnosticar_windows.bat para um relatorio completo.
pause
exit /b 1

:ERRO_FRONTEND
echo.
echo ============================================================
echo O FRONTEND NAO RESPONDEU NA PORTA 5500
echo ============================================================
echo Confira a janela "Frontend - Nucleo Batuira".
echo Log: backend\logs\ultimo_frontend.log
echo Execute diagnosticar_windows.bat para um relatorio completo.
pause
exit /b 1

:verificar_porta
netstat -ano | findstr /C:":%~1" | findstr /I "LISTENING" >nul 2>&1
if errorlevel 1 exit /b 0
exit /b 1

:testar_url
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r=Invoke-WebRequest -UseBasicParsing -Uri '%~1' -TimeoutSec 2; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
exit /b %errorlevel%
