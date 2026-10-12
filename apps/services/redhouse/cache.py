"""Caché de lectura privada; la revisión SQL cambia en la transacción propietaria."""

import hashlib
import json
from functools import wraps

from flask import current_app, g, request

from .codec import plain
from .db import transaction
from .security import key, redis_call


def cached_read(namespace, ttl=15):
    """Aplicar dentro de @endpoint: autenticación y auditoría preceden al HIT.

    El propietario instala su tabla cache_revision y sus triggers. No se comparte
    caché entre servicios ni se invalida antes de un commit. Una respuesta en vuelo
    puede llenar la generación antigua; ninguna lectura posterior al commit la usa.
    """

    def decorate(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if "no-cache" in request.headers.get("Cache-Control", ""):
                g.cache_status = "BYPASS"
                return fn(*args, **kwargs)
            with transaction() as conn:
                revision = conn.execute(
                    "SELECT revision FROM cache_revision WHERE name=%s", (namespace,)
                ).fetchone()["revision"]
            actor = g.actor
            identity = [
                current_app.config["SERVICE"],
                namespace,
                revision,
                actor["id"],
                actor["tenant_id"],
                actor["region_id"],
                actor["role"],
                actor.get("version"),
                request.path,
                sorted(request.args.lists()),
            ]
            digest = hashlib.sha256(
                json.dumps(identity, sort_keys=True).encode()
            ).hexdigest()
            cache_key = key(
                "cache:" + current_app.config["SERVICE"] + ":read:" + digest
            )
            raw = redis_call(lambda r: r.get(cache_key))
            if raw is not None:
                g.cache_hit, g.cache_status = True, "HIT"
                return json.loads(raw)
            g.cache_status = "MISS"
            result = plain(fn(*args, **kwargs))
            redis_call(lambda r: r.set(cache_key, json.dumps(result), ex=ttl))
            return result

        return wrapped

    return decorate
