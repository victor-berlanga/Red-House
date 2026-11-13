#!/bin/sh
set -eu
cd "$(dirname "$0")"
export PYINSTALLER_CONFIG_DIR="$PWD/.pyinstaller-cache"
.venv/bin/python -m PyInstaller --noconfirm --windowed --onedir --collect-all keyring --name RedHouse --add-data 'redhouse_desktop/contracts:redhouse_desktop/contracts' launch.py
