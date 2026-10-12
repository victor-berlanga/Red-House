#!/usr/bin/env bash
# Iniciar la plataforma ya preparada desde cualquier directorio.
set -euo pipefail
redhouse_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == '--help' || "${1:-}" == '-h' ]]; then
    exec bash "$redhouse_root/componentes.sh" --help
fi
exec bash "$redhouse_root/componentes.sh" todo "$@"
