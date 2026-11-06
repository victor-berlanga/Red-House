"""Amplía ACL existentes sin rotar claves, borrar sesiones ni reiniciar Redis."""

import json
from urllib.parse import urlsplit

import redis
from redhouse.config import SERVICES


def upgrade_acl(directory, state):
    with redis.Redis.from_url(
        state["redis_admin"], socket_connect_timeout=2, socket_timeout=3
    ) as admin:
        for service in SERVICES:
            config = json.loads((directory / (service + ".json")).read_text())
            username = urlsplit(config["REDIS_URL"]).username
            prefix = config["REDIS_PREFIX"]
            if not username or username == "default":
                raise RuntimeError(
                    "La ampliación requiere cuentas de servicio aisladas."
                )
            rules = [f"%R~{prefix}reauth:*"]
            if service == "identidad_acceso":
                rules += [
                    f"~{prefix}{area}:*"
                    for area in ("device", "mfa", "recovery", "reauth")
                ]
            if service == "transporte":
                rules += [
                    f"%R~{prefix}device:*",
                    f"~{prefix}tracking:*",
                    f"&{prefix}tracking:channel:*",
                    "+zadd",
                    "+zrem",
                    "+zremrangebyscore",
                    "+zscore",
                    "+zcard",
                    "+publish",
                ]
            admin.execute_command("ACL", "SETUSER", username, *rules)
        admin.execute_command("ACL", "SAVE")
