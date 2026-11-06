"""DTO de salida y precondiciones compartidas por ampliaciones v1."""

from redhouse.errors import APIError


def schema(model):
    """Inline Pydantic definitions for standalone per-operation response DTOs."""
    root = model.model_json_schema()

    def visit(value):
        if isinstance(value, list):
            return [visit(v) for v in value]
        if not isinstance(value, dict):
            return value
        if "$ref" in value:
            return visit(root["$defs"][value["$ref"].rsplit("/", 1)[-1]])
        return {k: visit(v) for k, v in value.items() if k != "$defs"}

    return visit(root)


def version(row, expected):
    if row["version"] != expected:
        raise APIError("stale_version", "Versión obsoleta; consulta el recurso.", 412)


def page_schema(model):
    return {
        "type": "object",
        "required": ["items", "page", "page_size", "total"],
        "properties": {
            "items": {"type": "array", "items": schema(model)},
            "page": {"type": "integer"},
            "page_size": {"type": "integer"},
            "total": {"type": "integer"},
        },
    }


def install_reads(app, path, table, model, roles, filters=None):
    """Solo lectura institucional; el módulo propietario define cada escritura."""
    from flask import g
    from .api import endpoint, listing
    from .db import transaction, get
    from .security import own

    # Lista permitida derivada del DTO público, nunca de nombres enviados por HTTP.
    fields = schema(model).get("properties", {})
    filters = dict(filters or {})
    searchable = tuple(
        k
        for k in ("name", "label", "identifier", "reference", "location", "source")
        if k in fields
    )
    filters.setdefault("q", searchable or ("id::text",))
    for name, definition in fields.items():
        if name.endswith("_id") and name not in ("tenant_id", "author_id"):
            filters.setdefault(name, (name, ()))
        if definition.get("type") == "boolean":
            filters.setdefault(name, (name, {"true": True, "false": False}))
        if definition.get("enum"):
            filters.setdefault(name, (name, tuple(definition["enum"])))
    dates = tuple(
        k
        for k in fields
        if k.endswith("_at")
        or k in ("valid_from", "valid_until", "starts_at", "ends_at")
    ) or ("created_at",)
    default_date = "created_at" if "created_at" in dates else dates[0]
    query = (*filters, "from_at", "until_at", "date_field", "sort")

    def list_rows():
        with transaction() as conn:
            return listing(
                conn,
                table,
                "tenant_id=%s",
                (g.actor["tenant_id"],),
                filters=filters,
                date_columns=dates,
                order=default_date + " DESC,id",
            )

    def detail(identifier):
        with transaction() as conn:
            row = get(conn, table, identifier)
            own(row["tenant_id"])
            return row

    list_rows.__name__, detail.__name__ = table + "_list", table + "_detail"
    endpoint(
        app,
        path,
        roles=roles,
        result=page_schema(model),
        paginated=True,
        query=query,
    )(list_rows)
    endpoint(app, path + "/<identifier>", roles=roles, result=schema(model))(detail)
