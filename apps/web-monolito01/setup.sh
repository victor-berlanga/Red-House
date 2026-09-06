#!/bin/sh
set -eu

red_house_dir=$(CDPATH= cd "$(dirname "$0")" && pwd)
if command -v python3 >/dev/null 2>&1; then
    exec python3 "$red_house_dir/scripts/setup_local.py" "$@"
fi
if command -v python >/dev/null 2>&1; then
    exec python "$red_house_dir/scripts/setup_local.py" "$@"
fi
printf '%s\n' 'Instala Python 3.12 o superior y PostgreSQL 14 o superior antes de continuar.' >&2
exit 1
