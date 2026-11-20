"""Revoca las sesiones vivas emitidas antes del acceso por aplicación.

Contexto: desde la migración compartida 22 cada sesión guarda la aplicación con la
que inició (`client`: web, desktop o mobile). Identidad ya rechaza, con 401, toda
sesión sin cliente (falla cerrada); este script las cierra de forma explícita al
publicar para que no queden filas vivas ni claves en Redis.

Efecto sobre las personas usuarias: quien tenía una sesión abierta debe iniciar
sesión de nuevo (el portal la redirige al login, el escritorio y el móvil piden
credenciales). No se tocan cuentas, roles, dispositivos ni datos de negocio.

Por omisión solo cuenta (--dry-run). Con --aplicar marca `revoked_at` en SQL y
borra `session:<id>` en Redis. Es idempotente: una segunda corrida encuentra 0.

    # laboratorio local (directorio de state.json)
    python -m scripts.revocar_sesiones_sin_cliente --directory .local/runtime --aplicar
    # Compose / VM: dentro de la imagen bootstrap (monta el directorio en /run/install
    # y alcanza PostgreSQL y Redis por la red `data`)
    docker compose --profile install run --rm --entrypoint python bootstrap \\
        -m scripts.revocar_sesiones_sin_cliente --directory /run/install [--aplicar]

Usa la configuración del propio servicio Identidad (`identidad_acceso.json`, en
`--directory` o en `--directory/apps`), el único con permiso de escritura sobre
sesiones; exige `REDIS_PREFIX` (no adivina el prefijo) y no imprime credenciales.
"""

import argparse
import json
from pathlib import Path

import psycopg
import redis

VIVAS_SIN_CLIENTE = (
    "SELECT id FROM sessions WHERE client IS NULL AND revoked_at IS NULL "
    "AND expires_at>now() ORDER BY id"
)


def sesiones_sin_cliente(conn):
    return [str(row[0]) for row in conn.execute(VIVAS_SIN_CLIENTE).fetchall()]


def revocar(conn, redis_client, prefix, ids):
    """Revoca en SQL y Redis; devuelve cuántas filas SQL cambió."""
    if not ids:
        return 0
    redis_client.delete(*(prefix + "session:" + sid for sid in ids))
    cursor = conn.execute(
        "UPDATE sessions SET revoked_at=now() WHERE id = ANY(%s::uuid[]) "
        "AND client IS NULL AND revoked_at IS NULL",
        (ids,),
    )
    return cursor.rowcount


def archivo_de_configuracion(directory):
    """`identidad_acceso.json` del laboratorio (directory/) o de Compose (directory/apps/)."""
    for candidate in (
        directory / "identidad_acceso.json",
        directory / "apps" / "identidad_acceso.json",
    ):
        if candidate.is_file():
            return candidate
    raise SystemExit(f"No se encontró identidad_acceso.json en {directory}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--directory", type=Path, required=True)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dry-run", action="store_true", help="solo contar (por omisión)"
    )
    group.add_argument("--aplicar", action="store_true", help="revocar de verdad")
    args = parser.parse_args(argv)
    config = json.loads(archivo_de_configuracion(args.directory).read_text())
    with psycopg.connect(config["DATABASE_URL"]) as conn:
        ids = sesiones_sin_cliente(conn)
        print(f"Sesiones vivas sin aplicación registrada: {len(ids)}")
        if not args.aplicar:
            print("Modo --dry-run: no se cambió nada. Usa --aplicar para revocarlas.")
            return 0
        client = redis.Redis.from_url(config["REDIS_URL"], decode_responses=True)
        changed = revocar(conn, client, config["REDIS_PREFIX"], ids)
        print(f"Sesiones revocadas: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
