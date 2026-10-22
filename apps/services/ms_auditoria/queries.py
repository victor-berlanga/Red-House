"""Consulta regional con una sola semántica para listado, conteo y exportación."""

from flask import g, request
from redhouse.api import pagination
from redhouse.audit_catalog import ACTIONS, CATEGORIES, RESULTS, describe
from redhouse.errors import APIError
from redhouse.models import utc_date, validate_id

FILTERS = (
    "from",
    "to",
    "categories",
    "action",
    "actor",
    "institution_id",
    "resource",
    "result",
    "correlation_id",
    "q",
)
DEFAULT_CATEGORIES = ("BUSINESS", "DECISION", "SECURITY")
MAX_EXPORT = 5000


def _case(position, default):
    def quote(value):
        return "'" + value.replace("'", "''") + "'"

    return (
        "CASE action "
        + " ".join(
            "WHEN " + quote(code) + " THEN " + quote(values[position])
            for code, values in ACTIONS.items()
        )
        + " ELSE "
        + quote(default)
        + " END"
    )


BASE = (
    """WITH audit AS (SELECT a.*,
 event_time(event->>'occurred_at') AS executed_at,
 event->>'resource_id' AS resource_id,
 event->>'correlation_id' AS correlation_id,
 event#>>'{metadata,audit,actor_name}' AS actor_name,
 event#>>'{metadata,audit,actor_role}' AS actor_role,
 event#>>'{metadata,audit,actor_institution_id}' AS actor_institution_id,
 event#>>'{metadata,audit,resource_folio}' AS resource_folio,
 event#>>'{metadata,audit,reason}' AS reason,
 COALESCE(event#>'{metadata,audit,changes}','{}'::jsonb) AS changes,
 COALESCE(event#>'{metadata,audit,changed_fields}','[]'::jsonb) AS changed_fields,
 jsonb_build_array(event->>'resource_id',event#>>'{metadata,request_id}',event#>>'{metadata,resource_id}',event#>>'{metadata,reservation_id}',event#>>'{metadata,shipment_id}',event#>>'{metadata,evaluation_id}',event#>>'{metadata,donation_id}',event#>>'{metadata,operation_id}') ||
 CASE WHEN jsonb_typeof(event#>'{metadata,audit,related_resources}')='array' THEN event#>'{metadata,audit,related_resources}' ELSE '[]'::jsonb END AS resource_refs,
 """
    + _case(1, "TECHNICAL")
    + " AS category,"
    + _case(2, "UNKNOWN")
    + " AS result FROM audit_events a WHERE region_id=%s) "
)


def present(row, compact=False):
    row = dict(row)
    row["action_label"] = describe(row["action"])[0]
    row["category_label"] = CATEGORIES[row["category"]]
    row["result_label"] = RESULTS[row["result"]]
    row["actor_display"] = (
        "Identidad no verificada"
        if row["action"] == "LOGIN_FAILED"
        else row.get("actor_name")
        or (str(row["actor_id"]) if row["actor_id"] else "Responsable no registrado")
    )
    row["resource_display"] = (
        row.get("resource_folio") or row.get("resource_id") or "Recurso no registrado"
    )
    if compact:
        return {
            k: row[k]
            for k in (
                "id",
                "action",
                "action_label",
                "actor_display",
                "tenant_id",
                "resource_display",
                "executed_at",
                "result_label",
                "category_label",
                "created_at",
            )
        }
    return row


def filters():
    page, size, offset = pagination(FILTERS)
    values, clauses = [g.actor["region_id"]], []
    args = {name: request.args.get(name, "").strip() for name in FILTERS}
    if any(len(value) > 200 for value in args.values()):
        raise APIError("validation", "Acorta los filtros a 200 caracteres.", 422)
    categories = (
        args["categories"].split(",")
        if args["categories"]
        else list(DEFAULT_CATEGORIES)
    )
    if categories == ["ALL"]:
        categories = list(CATEGORIES)
    elif categories == ["NONE"]:
        categories = []
    if set(categories) - set(CATEGORIES):
        raise APIError("validation", "Selecciona categorías de auditoría válidas.", 422)
    clauses.append("category = ANY(%s)")
    values.append(categories)
    dates = {}
    for name, comparison in (("from", ">="), ("to", "<=")):
        if args[name]:
            dates[name] = utc_date(args[name], name)
            clauses.append("executed_at " + comparison + " %s")
            values.append(dates[name])
    if "from" in dates and "to" in dates and dates["from"] > dates["to"]:
        raise APIError(
            "validation", "La fecha inicial no puede ser posterior a la final.", 422
        )
    for name, column in (
        ("action", "action"),
        ("result", "result"),
        ("institution_id", "tenant_id"),
        ("correlation_id", "correlation_id"),
    ):
        if args[name]:
            if name in ("institution_id", "correlation_id"):
                validate_id(args[name])
            if name == "result" and args[name] not in RESULTS:
                raise APIError("validation", "Selecciona un resultado válido.", 422)
            clauses.append(column + "=%s")
            values.append(args[name])
    for name, expression in (
        ("actor", "(actor_name ILIKE %s OR actor_id::text ILIKE %s)"),
        (
            "resource",
            "(resource_folio ILIKE %s OR resource_id ILIKE %s OR resource_refs ? %s)",
        ),
        ("q", "(action ILIKE %s OR resource_folio ILIKE %s OR resource_id ILIKE %s)"),
    ):
        if args[name]:
            pattern = (
                "%"
                + args[name]
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
                + "%"
            )
            clauses.append(expression)
            values.extend(
                [pattern, pattern, args[name]]
                if name == "resource"
                else [pattern] * expression.count("%s")
            )
    return page, size, offset, " AND ".join(clauses), values


def listing(conn, export=False):
    page, size, offset, condition, values = filters()
    conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
    total = conn.execute(
        BASE + "SELECT count(*) AS n FROM audit WHERE " + condition, values
    ).fetchone()["n"]
    if export and total > MAX_EXPORT:
        raise APIError(
            "export_limit",
            f"Hay {total} resultados. Reduce los filtros a un máximo de {MAX_EXPORT} para exportarlos.",
            422,
        )
    rows = conn.execute(
        BASE
        + "SELECT * FROM audit WHERE "
        + condition
        + " ORDER BY executed_at DESC NULLS LAST,created_at DESC,id LIMIT %s OFFSET %s",
        [*values, MAX_EXPORT if export else size, 0 if export else offset],
    ).fetchall()
    return {
        "items": [present(row, compact=export) for row in rows],
        "page": 1 if export else page,
        "page_size": MAX_EXPORT if export else size,
        "total": total,
    }


def event(conn, identifier):
    validate_id(identifier)
    row = conn.execute(
        BASE + "SELECT * FROM audit WHERE id=%s", (g.actor["region_id"], identifier)
    ).fetchone()
    if row is None:
        raise APIError(
            "not_found", "Evento no disponible en tu ámbito autorizado.", 404
        )
    return present(row)


def related(conn, identifier):
    conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
    seed = event(conn, identifier)
    refs = {
        v for v in seed["resource_refs"] if isinstance(v, str) and v != "collection"
    }
    found, limited = {str(seed["id"]): seed}, False
    for _ in range(4):
        rows = conn.execute(
            BASE
            + "SELECT * FROM audit WHERE resource_refs ?| %s OR correlation_id=%s ORDER BY executed_at NULLS LAST,created_at,id LIMIT 501",
            (g.actor["region_id"], sorted(refs), seed["correlation_id"]),
        ).fetchall()
        limited = len(rows) > 500
        for row in rows[:500]:
            found[str(row["id"])] = present(row)
        expanded = refs | {
            value
            for row in found.values()
            for value in row["resource_refs"]
            if isinstance(value, str) and value != "collection"
        }
        if expanded == refs or limited:
            break
        refs = expanded
    else:
        limited = True
    items = sorted(
        found.values(),
        key=lambda row: (
            str(row["executed_at"] or "9999"),
            str(row["created_at"]),
            str(row["id"]),
        ),
    )
    return {
        "items": items[:500],
        "limited": limited or len(items) > 500,
        "limit": 500,
        "max_hops": 4,
    }
