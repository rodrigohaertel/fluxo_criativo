@echo off
setlocal enabledelayedexpansion

echo ==========================================================
echo    trafego - Instalador (Windows)
echo ==========================================================
echo.

REM Prefere py -3.12 se disponivel (launcher oficial Python Windows); fallback python
set PY_BIN=
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set PY_BIN=py -3.12
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo [ERRO] Python nao encontrado.
        echo        Instale em: https://www.python.org/downloads/ ^(recomendado 3.12^)
        exit /b 1
    )
    set PY_BIN=python
)

for /f "tokens=2" %%v in ('%PY_BIN% --version 2^>^&1') do set PY_VERSION=%%v
echo [OK] Python %PY_VERSION% ^(via %PY_BIN%^)

if not exist ".venv" (
    echo [..] Criando virtualenv em .venv\
    %PY_BIN% -m venv .venv
)

call .venv\Scripts\activate.bat
echo [OK] Virtualenv ativado

python -m pip install --upgrade pip --quiet

echo [..] Instalando dependencias (pode levar 1-2 min)...
python -m pip install -e ".[web]" --quiet

echo.
echo ==========================================================
echo   Instalacao concluida!
echo ==========================================================
echo.
echo   Proximos passos:
echo.
echo   1) Ative o ambiente (sempre antes de usar):
echo      .venv\Scripts\activate.bat
echo.
echo   2) Configure sua conta:
echo      trafego setup
echo.
echo   3) Primeira analise:
echo      trafego
echo.
echo   4) Ou abra a UI Web:
echo      trafego web
echo.
echo   Docs: docs\PRIMEIRO_USO.md
echo.
echo ==========================================================

endlocal
