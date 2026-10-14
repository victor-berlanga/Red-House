@echo off
setlocal DisableDelayedExpansion
if /i "%~1"=="--help" goto help
if /i "%~1"=="-h" goto help
where wsl.exe >nul 2>&1
if errorlevel 1 goto missing_wsl
wsl.exe --cd "%~dp0." --exec bash ./components.sh %*
exit /b %errorlevel%

:help
echo Uso: components.bat [COMPONENTE ^| ACCION [COMPONENTE]] [opciones]
echo Sin argumentos: menu interactivo. Requiere WSL y el entorno preparado.
echo Componentes: todo, ms, web, bases o nombre de microservicio.
echo Acciones: listar, estado, detener [COMPONENTE], reiniciar [COMPONENTE].
echo Opciones: --directory RUTA_LINUX, --web-port PUERTO.
echo Las rutas relativas parten de la raiz del repositorio.
echo Ejemplos: components.bat inventario
echo           components.bat reiniciar donantes
echo           components.bat detener todo
echo Instalacion y preparacion: install.bat
exit /b 0

:missing_wsl
echo Falta WSL. Consulta documentation/markdowns/Instalacion_y_operacion.md. >&2
exit /b 1
