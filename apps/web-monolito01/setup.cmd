@echo off
setlocal DisableDelayedExpansion
where py >nul 2>&1
if errorlevel 1 goto try_python
py -3 "%~dp0scripts\setup_local.py" %*
exit /b %errorlevel%

:try_python
where python >nul 2>&1
if errorlevel 1 goto missing_python
python "%~dp0scripts\setup_local.py" %*
exit /b %errorlevel%

:missing_python
echo Instala Python 3.12 o superior y PostgreSQL 14 o superior antes de continuar.
exit /b 1
