@echo off
setlocal DisableDelayedExpansion
if /i "%~1"=="--help" goto help
if /i "%~1"=="-h" goto help
where wsl.exe >nul 2>&1
if errorlevel 1 goto missing_wsl
wsl.exe --cd "%~dp0." --exec bash ./start.sh %*
exit /b %errorlevel%

:help
echo Uso: start.bat [--directory RUTA_LINUX] [--web-port PUERTO]
echo Inicia la plataforma preparada mediante WSL, sin instalar paquetes.
echo Preparacion inicial: install.bat
echo Menu y operaciones individuales: components.bat
echo Las rutas relativas parten de la raiz del repositorio.
exit /b 0

:missing_wsl
echo Falta WSL. Consulta documentation/markdowns/Instalacion_y_operacion.md. >&2
exit /b 1
