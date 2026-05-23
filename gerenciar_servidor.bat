@echo off
chcp 65001 > nul
title Gerenciador ViagensLabs

:menu
cls
echo =================================================================
echo             GERENCIADOR DO SERVIDOR VIAGENSLABS (FASTAPI)
echo =================================================================
echo.
echo [1] Iniciar/Reiniciar Servidor (Modo Reload - Desenvolvimento)
echo [2] Iniciar Servidor (Modo Producao - Sem Reload)
echo [3] Parar Servidor (Derrubar processos na porta 8000)
echo [4] Sair
echo.
echo =================================================================
set /p opcao="Escolha uma opcao (1-4): "

if "%opcao%"=="1" goto iniciar_dev
if "%opcao%"=="2" goto iniciar_prod
if "%opcao%"=="3" goto parar
if "%opcao%"=="4" exit
goto menu

:iniciar_dev
cls
echo =================================================================
echo    INICIANDO SERVIDOR EM MODO DESENVOLVIMENTO (AUTO-RELOAD)
echo =================================================================
echo.
echo [1/3] Liberando a porta 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
    echo [INFO] Processo antigo PID %%a encerrado.
)
echo [INFO] Porta 8000 liberada com sucesso.
echo.
echo [2/3] Verificando ambiente virtual (venv)...
if not exist "venv\Scripts\python.exe" (
    echo [ERRO] O ambiente virtual 'venv' nao foi encontrado nesta pasta!
    echo Pressione qualquer tecla para voltar ao menu.
    pause > nul
    goto menu
)
echo.
echo [3/3] Iniciando Uvicorn...
echo.
echo =================================================================
echo SERVIDOR ATIVO EM: http://localhost:8000
echo =================================================================
echo.
set PYTHONPATH=.
set GOOGLE_CLOUD_PROJECT=maga-bigdata
venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
goto menu

:iniciar_prod
cls
echo =================================================================
echo         INICIANDO SERVIDOR EM MODO PRODUCAO (ESTAVEL)
echo =================================================================
echo.
echo [1/3] Liberando a porta 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
    echo [INFO] Processo antigo PID %%a encerrado.
)
echo.
echo [2/3] Verificando ambiente virtual...
if not exist "venv\Scripts\python.exe" (
    echo [ERRO] O ambiente virtual 'venv' nao foi encontrado!
    pause
    goto menu
)
echo.
echo [3/3] Iniciando Uvicorn (Producao)...
echo.
echo =================================================================
echo SERVIDOR ATIVO EM: http://localhost:8000
echo =================================================================
echo.
set PYTHONPATH=.
set GOOGLE_CLOUD_PROJECT=maga-bigdata
venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
pause
goto menu

:parar
cls
echo =================================================================
echo               PARANDO SERVIDOR VIAGENSLABS
echo =================================================================
echo.
echo Localizando e encerrando processos na porta 8000...
set "encerrado=0"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
    echo [INFO] Processo PID %%a parado com sucesso.
    set "encerrado=1"
)
if "%encerrado%"=="0" (
    echo [INFO] Nenhum processo ativo encontrado rodando na porta 8000.
) else (
    echo [INFO] Servidor parado com sucesso.
)
echo.
echo Pressione qualquer tecla para retornar ao menu.
pause > nul
goto menu
