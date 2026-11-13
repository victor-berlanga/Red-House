@echo off
cd /d "%~dp0"
set "PYINSTALLER_CONFIG_DIR=%CD%\.pyinstaller-cache"
.venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --onedir --collect-all keyring --name RedHouse --add-data "redhouse_desktop/contracts:redhouse_desktop/contracts" launch.py
exit /b %errorlevel%
