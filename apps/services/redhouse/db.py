import atexit
import logging
from contextlib import contextmanager
from threading import Lock

import psycopg
from flask import current_app
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .errors import APIError
from .shared import service_schema

_pool_lock = Lock()


def connection_scope():
    """Optional bounded pool, separated by application, credential and schema."""
    cfg = current_app.config
    kwargs = {
        "row_factory": dict_row,
        "connect_timeout": 2,
        "options": f"-c search_path={service_schema(cfg['SERVICE'])},pg_catalog -c statement_timeout=5000 -c lock_timeout=3000 -c timezone=UTC",
    }
    size = cfg.get("DATABASE_POOL_SIZE", 0)
    if not size:
        return psycopg.connect(cfg["DATABASE_URL"], **kwargs)
    from psycopg_pool import ConnectionPool

    with _pool_lock:
        pools = current_app.extensions.setdefault("database_pools", {})
        identity = (cfg["DATABASE_URL"], cfg["SERVICE"], size)
        if identity not in pools:
            pool = ConnectionPool(
                cfg["DATABASE_URL"],
                kwargs=kwargs,
                min_size=0,
                max_size=size,
                timeout=2,
                max_waiting=16,
                max_idle=30,
                num_workers=1,
                check=ConnectionPool.check_connection,
                open=True,
                name=cfg["SERVICE"],
            )
            pools[identity] = pool
            atexit.register(pool.close)
        return pools[identity].connection(timeout=2)


@contextmanager
def transaction():
    try:
        with connection_scope() as conn:
            yield conn
    except psycopg.errors.UniqueViolation:
        raise APIError("conflict", "El registro u operación ya existe.", 409) from None
    except psycopg.errors.ForeignKeyViolation:
        raise APIError(
            "reference_conflict",
            "La operación referencia un registro inexistente o todavía relacionado.",
            409,
        ) from None
    except psycopg.errors.CheckViolation:
        raise APIError(
            "constraint_conflict",
            "La operación no cumple las restricciones de integridad.",
            409,
        ) from None
    except (
        psycopg.errors.LockNotAvailable,
        psycopg.errors.SerializationFailure,
        psycopg.errors.DeadlockDetected,
    ):
        raise APIError(
            "concurrency",
            "Operación concurrente; consulta el estado y vuelve a intentar.",
            409,
        ) from None
    except psycopg.OperationalError as exc:
        logging.getLogger("redhouse.database").warning(
            "database_unavailable service=%s type=%s sqlstate=%s",
            current_app.config["SERVICE"],
            type(exc).__name__,
            exc.sqlstate,
        )
        raise APIError(
            "database_unavailable", "Almacenamiento temporalmente inaccesible.", 503
        ) from None


def get(conn, table, identifier, lock=False):
    from psycopg import sql

    from .models import validate_id

    validate_id(identifier)
    query = sql.SQL(
        "SELECT * FROM {} WHERE id=%s" + (" FOR UPDATE" if lock else "")
    ).format(sql.Identifier(table))
    row = conn.execute(query, (identifier,)).fetchone()
    if not row:
        raise APIError("not_found", "Recurso inexistente.", 404)
    return row


def insert(conn, table, fields):
    from psycopg import sql

    names = list(fields)
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
        sql.Identifier(table),
        sql.SQL(",").join(map(sql.Identifier, names)),
        sql.SQL(",").join(sql.Placeholder() for _ in names),
    )
    return conn.execute(
        query, [Jsonb(x) if isinstance(x, (dict, list)) else x for x in fields.values()]
    ).fetchone()


def update(conn, table, identifier, fields):
    from psycopg import sql

    query = sql.SQL("UPDATE {} SET {} WHERE id=%s RETURNING *").format(
        sql.Identifier(table),
        sql.SQL(",").join(sql.SQL("{}=%s").format(sql.Identifier(k)) for k in fields),
    )
    return conn.execute(
        query,
        [Jsonb(v) if isinstance(v, (dict, list)) else v for v in fields.values()]
        + [identifier],
    ).fetchone()
