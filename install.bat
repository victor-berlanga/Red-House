@echo off
setlocal DisableDelayedExpansion
rem El gestor integrado requiere Linux: ejecutar en la distribucion WSL predeterminada.
if /i "%~1"=="--help" goto help
if /i "%~1"=="-h" goto help
where wsl.exe >nul 2>&1
if errorlevel 1 goto missing_wsl
echo Preparando Red House dentro de WSL; las dependencias deben estar instaladas en Linux.
wsl.exe --cd "%~dp0." --exec bash ./install.sh %*
exit /b %errorlevel%

:help
echo Uso: install.bat [--directory RUTA_LINUX] [--no-install]
echo Prepara dependencias Python y configuracion mediante WSL.
echo Python requiere venv y ensurepip en esa distribucion Linux.
echo Requiere WSL 2 y Python 3.12+, PostgreSQL 14, Redis 7+ y MongoDB 8.0 en Linux.
echo Las rutas relativas parten de la raiz del repositorio.
echo No inicia las aplicaciones. Despues ejecuta: start.bat
echo Guia: apps/services/docs/ARRANQUE_LOCAL.md
exit /b 0

:missing_wsl
echo Falta WSL. Instala WSL 2 y configura una distribucion Linux predeterminada. >&2
echo Consulta apps/services/docs/ARRANQUE_LOCAL.md antes de instalar dependencias. >&2
exit /b 1
