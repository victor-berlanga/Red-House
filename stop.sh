#!/usr/bin/env bash
# Detener el entorno completo conservando sus datos.
set -euo pipefail
redhouse_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == '--help' || "${1:-}" == '-h' ]]; then
    cat <<'HELP'
Uso: bash stop.sh [--directory RUTA]
Detiene la web, las API, sus workers, PostgreSQL, Redis y MongoDB del entorno.
Conserva los datos y no detiene procesos ajenos al proyecto.
Directorio predeterminado: .local/runtime del repositorio.
HELP
    exit 0
fi
exec bash "$redhouse_root/components.sh" detener todo "$@"
