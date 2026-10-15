import hashlib
import json
import re
from functools import wraps
from uuid import uuid4

from flask import current_app, g, request
from psycopg.types.json import Jsonb

from .codec import parse, plain, respond
from .db import transaction
from .errors import APIError
from .events import audit_read
from .security import authenticate, internal_auth, rate_limit


def endpoint(
    app,
    path,
    method="GET",
    *,
    model=None,
    roles=(),
    internal=(),
    public=False,
    delegate=True,
    summary="",
    status=200,
    result=None,
    paginated=False,
    query=(),
):
    def decorator(fn):
        @wraps(fn)
        def wrapped(**params):
            if not public:
                try:
                    if internal:
                        internal_auth(internal)
                    if not internal or delegate:
                        authenticate(roles)
                except APIError:
                    rate_limit()
                    raise
                if internal:
                    rate_limit("service", g.caller)
                else:
                    rate_limit("user", g.actor["tenant_id"] + ":" + g.actor["id"])
                if method == "GET":
                    try:
                        audit_read(next(iter(params.values()), "collection"))
                    except APIError as exc:
                        if (
                            current_app.config["SERVICE"] != "monitoreo"
                            or path != "/api/v1/status"
                            or exc.code != "database_unavailable"
                        ):
                            raise
                        current_app.logger.warning(
                            "monitor_status_read_sql_audit_unavailable"
                        )
            elif path.startswith("/api/"):
                rate_limit()
            data = parse(model) if model else None
            output = fn(data=data, **params) if model else fn(**params)
            return respond(
                {
                    "data": output,
                    "meta": {
                        "correlation_id": g.correlation_id,
                        "service": current_app.config["SERVICE"],
                        "version": current_app.config["VERSION"],
                    },
                },
                status,
            )

        app.add_url_rule(
            path, endpoint=fn.__name__, view_func=wrapped, methods=[method]
        )
        app.extensions["contracts"].append(
            {
                "path": path,
                "method": method,
                "model": model,
                "roles": roles,
                "internal": internal,
                "delegate": delegate,
                "public": public,
                "summary": summary or fn.__name__,
                "status": status,
                "result": result,
                "paginated": paginated,
                "query": query,
                "name": fn.__name__,
            }
        )
        return fn

    return decorator


def atomic(operation, data, fn):
    """Resultado y efectos SQL atómicos; la misma clave con otro cuerpo es 409."""
    idem = request.headers.get("Idempotency-Key", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,100}", idem):
        raise APIError(
            "idempotency_required",
            "Idempotency-Key de 8–100 caracteres requerido.",
            400,
        )
    fingerprint = hashlib.sha256(
        json.dumps({"operation": operation, "input": data}, sort_keys=True).encode()
    ).hexdigest()
    user = g.actor["id"]
    with transaction() as conn:
        lock = int.from_bytes(
            hashlib.sha256(
                (current_app.config["SERVICE"] + ":" + user + ":" + idem).encode()
            ).digest()[:8],
            "big",
            signed=True,
        )
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (lock,))
        old = conn.execute(
            "SELECT * FROM idempotency WHERE user_id=%s AND key=%s", (user, idem)
        ).fetchone()
        if old:
            if old["fingerprint"] != fingerprint:
                raise APIError(
                    "idempotency_conflict",
                    "Clave utilizada para otra operación o contenido.",
                    409,
                )
            return old["result"]
        result = plain(fn(conn))
        conn.execute(
            "INSERT INTO idempotency(id,user_id,key,operation,fingerprint,result) VALUES(%s,%s,%s,%s,%s,%s)",
            (str(uuid4()), user, idem, operation, fingerprint, Jsonb(result)),
        )
        return result


def pagination(extra=()):
    if set(request.args) - {"page", "page_size", *extra}:
        raise APIError("validation", "Parámetro de consulta desconocido.")
    for name in request.args:
        if len(request.args.getlist(name)) != 1:
            raise APIError("validation", "Parámetro de consulta duplicado.")
    try:
        page = int(request.args.get("page", "1"))
        size = int(request.args.get("page_size", "20"))
        if page < 1 or page > 100000 or not 1 <= size <= 100:
            raise ValueError()
    except ValueError:
        raise APIError("validation", "Paginación inválida.") from None
    return page, size, (page - 1) * size


def listing(
    conn, table, where, values, *, order="created_at DESC,id", columns="*", filters=None
):
    # Tabla, columnas, condición y orden son constantes de módulos, nunca entradas HTTP.
    filters = filters or {}
    page, size, offset = pagination(filters)
    where, values = "(" + where + ")", list(values)
    for name, config in filters.items():
        value = request.args.get(name, "").strip()
        if not value:
            continue
        if len(value) > 100:
            raise APIError("validation", "Filtro demasiado largo.")
        if name == "q":
            where += (
                " AND (" + " OR ".join(column + " ILIKE %s" for column in config) + ")"
            )
            escaped = (
                value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            )
            values.extend(["%" + escaped + "%"] * len(config))
        else:
            column, allowed = config
            if allowed and value not in allowed:
                raise APIError("validation", "Valor de filtro inválido.")
            if isinstance(allowed, dict):
                value = allowed[value]
            if name.endswith("_id"):
                from .models import validate_id

                validate_id(value)
            where += " AND " + column + "=%s"
            values.append(value)
    count = conn.execute(
        f"SELECT count(*) AS n FROM {table} WHERE {where}", values
    ).fetchone()["n"]
    rows = conn.execute(
        f"SELECT {columns} FROM {table} WHERE {where} ORDER BY {order} LIMIT %s OFFSET %s",
        (*values, size, offset),
    ).fetchall()
    return {"items": rows, "page": page, "page_size": size, "total": count}
