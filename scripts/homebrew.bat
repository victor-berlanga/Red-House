@echo off
setlocal DisableDelayedExpansion
rem homebrew.sh es un auxiliar del instalador automatico para macOS.
echo Homebrew no se utiliza en la version Windows de Red House. >&2
echo Instala las dependencias dentro de tu distribucion WSL y ejecuta install.bat. >&2
echo Consulta apps/services/docs/ARRANQUE_LOCAL.md. >&2
exit /b 1
