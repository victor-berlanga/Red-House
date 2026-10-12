#!/usr/bin/env bash
# Menú/CLI local. Los argumentos se reenvían como array, nunca mediante eval.
set -euo pipefail
redhouse_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ $# -eq 0 ]]; then
    printf '\nRed House\n1) Iniciar todo\n2) Iniciar todos los microservicios\n3) Iniciar solo la web\n4) Elegir un microservicio\n5) Iniciar bases de datos\n6) Consultar estado\n7) Detener todo\n0) Salir\n'
    read -r -p 'Opción: ' redhouse_option || exit 0
    case "$redhouse_option" in
        1) set -- todo ;; 2) set -- ms ;; 3) set -- web ;;
        4) printf '%s\n' 'identidad_acceso donantes receptores inventario compatibilidad priorizacion_geografia transporte custodia alertas auditoria monitoreo'
           read -r -p 'Nombre del servicio: ' redhouse_service || exit 0
           set -- "$redhouse_service" ;;
        5) set -- bases ;; 6) set -- estado ;; 7) set -- detener todo ;;
        0) exit 0 ;; *) printf 'Opción inválida.\n' >&2; exit 2 ;;
    esac
fi
if [[ "$1" == '--help' || "$1" == '-h' ]]; then
    cat <<'HELP'
Uso: bash start.sh [--directory RUTA] [--web-port 5050]
     bash stop.sh [--directory RUTA]
     bash components.sh [COMPONENTE | ACCIÓN [COMPONENTE]] [opciones]
Sin argumentos: menú interactivo.
Componentes: todo, ms, web, bases o nombre de microservicio (listar).
Acciones: estado, listar, detener [todo|ms|web|SERVICIO],
          reiniciar [todo|ms|web|SERVICIO].
Opciones: --directory RUTA (predeterminado: .local/demo del repositorio),
          --web-port PUERTO.
Ejemplos: bash components.sh inventario
          bash components.sh reiniciar donantes
Instalación y preparación (una vez): bash install.sh
Estos comandos solo operan el entorno existente; no revisan ni instalan paquetes.
HELP
    exit 0
fi
if [[ "$1" == 'preparar' ]]; then
    printf 'Para instalar o preparar el entorno ejecuta: bash install.sh
' >&2
    exit 2
fi
redhouse_python="$redhouse_root/apps/services/.venv/bin/python"
if [[ ! -x "$redhouse_python" ]]; then
    printf 'Falta el entorno Python. Ejecuta primero: bash install.sh
' >&2
    exit 1
fi
exec "$redhouse_python" "$redhouse_root/scripts/manage.py" "$@"
