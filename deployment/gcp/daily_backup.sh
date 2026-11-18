#!/bin/sh
# Respaldo diario de la VM: PostgreSQL, MongoDB, Redis y configuración privada,
# con restauración de prueba en contenedores aislados (--verify).
# Lo ejecuta redhouse-backup.timer. Las aplicaciones se detienen durante el
# respaldo (unos minutos) y backup.py las vuelve a iniciar en orden.
# TRABAJO FUTURO: no está instalado en la VM. Por decisión del equipo (18/11/2026) el
# respaldo se corre a mano antes de cada cambio y antes de la presentación.
set -eu
ROOT=/opt/redhouse
DIRECTORY=$ROOT/.local/compose
BACKUPS=$DIRECTORY/backups
KEEP=${REDHOUSE_BACKUP_KEEP:-7}
MIN_FREE_KB=${REDHOUSE_BACKUP_MIN_FREE_KB:-1500000}

free_kb=$(df -Pk "$BACKUPS" | awk 'NR==2 {print $4}')
if [ "$free_kb" -lt "$MIN_FREE_KB" ]; then
    echo "Respaldo omitido: solo quedan ${free_kb} KB libres (mínimo ${MIN_FREE_KB})." >&2
    exit 1
fi

/usr/bin/python3 "$ROOT/deployment/backup.py" \
    --directory "$DIRECTORY" \
    --verify \
    --output "$BACKUPS/ultimo-respaldo.json"

# Conservar solo los KEEP respaldos diarios más recientes (carpetas AAAAMMDDTHHMMSSZ).
# Las carpetas con otro nombre (respaldos manuales previos a un cambio) no se tocan.
ls -1d "$BACKUPS"/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]T[0-9][0-9][0-9][0-9][0-9][0-9]Z 2>/dev/null \
    | sort -r | tail -n +"$((KEEP + 1))" | while read -r old; do
        rm -rf -- "$old"
    done
