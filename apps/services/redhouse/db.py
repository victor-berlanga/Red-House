from contextlib import contextmanager

import psycopg
from flask import current_app
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .errors import APIError
from .shared import service_schema


@contextmanager
def transaction():
    try:
        with psycopg.connect(
            current_app.config["DATABASE_URL"],
            row_factory=dict_row,
            connect_timeout=2,
            options=f"-c search_path={service_schema(current_app.config['SERVICE'])},pg_catalog -c statement_timeout=5000 -c lock_timeout=3000 -c timezone=UTC",
        ) as conn:
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
    except psycopg.OperationalError:
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
