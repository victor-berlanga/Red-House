#!/usr/bin/env bash
# Instalar dependencias y preparar la configuración, sin iniciar las aplicaciones.
set -euo pipefail
redhouse_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == '--help' || "${1:-}" == '-h' ]]; then
    cat <<'HELP'
Uso: bash install.sh [--directory RUTA] [--no-install]
Instala dependencias faltantes y prepara el entorno (predeterminado: .local/demo).
--no-install: comprobar/preparar usando únicamente dependencias ya instaladas.
En un entorno nuevo las bases se encienden para inicializarlo y se detienen al terminar.
No inicia las aplicaciones. Después ejecuta: bash start.sh
HELP
    exit 0
fi
redhouse_python=''
for redhouse_candidate in "$redhouse_root/apps/services/.venv/bin/python" python3.12 python3 /opt/homebrew/bin/python3.12 /usr/local/bin/python3.12; do
    if "$redhouse_candidate" -c 'import sys; sys.exit(sys.version_info < (3,12))' >/dev/null 2>&1; then
        redhouse_python="$redhouse_candidate"
        break
    fi
done
if [[ -z "$redhouse_python" ]]; then
    for redhouse_argument in "$@"; do
        if [[ "$redhouse_argument" == '--no-install' ]]; then
            printf 'Falta Python 3.12+ ejecutable. Instálalo con soporte venv/ensurepip y añádelo al PATH; en Windows debe estar instalado dentro de WSL.\n' >&2; exit 1
        fi
    done
    if [[ "$(uname -s)" != Darwin ]]; then
        printf 'Falta Python 3.12+ ejecutable. Instálalo junto con el paquete venv de la misma versión y añádelo al PATH. En Windows instala estos paquetes dentro de WSL. Si no tienes permisos, solicita la instalación al administrador y repite el instalador.\n' >&2; exit 1
    fi
    source "$redhouse_root/scripts/homebrew.sh"
    redhouse_find_brew
    if ! "$redhouse_brew" install python@3.12; then
        printf 'No se pudo instalar Python 3.12 con Homebrew. Revisa el error anterior (permisos, red o herramientas faltantes), corrígelo y repite bash install.sh.\n' >&2
        exit 1
    fi
    redhouse_python="$("$redhouse_brew" --prefix python@3.12)/bin/python3.12"
fi
exec "$redhouse_python" "$redhouse_root/scripts/manage.py" preparar "$@"
