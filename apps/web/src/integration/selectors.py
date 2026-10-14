"""Búsqueda paginada para formularios; destinos HTTP definidos, nunca URLs del usuario."""

from flask import Blueprint, g, jsonify, request, url_for
from ..access import BusinessError
from .client import call

bp = Blueprint("selectors", __name__)
SOURCES = {
    "donors": ("donantes", "donors", "display_name", {}),
    "eligible-donors": ("donantes", "donors", "display_name", {"status": "ELIGIBLE"}),
    "recipients": ("receptores", "recipients", "display_name", {}),
    "donations-blood": (
        "donantes",
        "donations",
        "id",
        {"kind": "BLOOD", "status": "PROCESSED"},
    ),
    "donations-organ": (
        "donantes",
        "donations",
        "id",
        {"kind": "ORGAN", "status": "PROCESSED"},
    ),
    "campaigns": ("donantes", "campaigns", "title", {}),
    "reservations": (
        "inventario",
        "reservations",
        "id",
        {"status": "RESERVED", "unplanned": "true"},
    ),
    "transport": ("identidad_acceso", "users", "username", {"role": "TRANSPORT"}),
    "locations": (
        "identidad_acceso",
        "catalogues/locations",
        "name",
        {"active": "true"},
    ),
}


def fetch(source, page=1, query=""):
    if source not in SOURCES:
        raise BusinessError("Selector no disponible.", 404)
    if page < 1 or page > 100000 or len(query) > 100:
        raise BusinessError("Búsqueda inválida.", 422)
    service, path, label, params = SOURCES[source]
    value = call(
        service,
        "/api/v1/" + path,
        params={**params, "page": page, "page_size": 20, "q": query},
    )
    items = [
        {"id": r["id"], "label": r.get(label) or r.get("folio") or r["id"]}
        for r in value["items"]
    ]
    return {
        "items": items,
        "page": page,
        "total": value["total"],
        "has_more": page * 20 < value["total"],
    }


def selection(name, label, source, default="", required=True):
    data = fetch(source)
    options = [(r["id"], r["label"]) for r in data["items"]]
    # Un identificador ya seleccionado no desaparece por estar en otra página.
    if default and not any(code == default for code, text in options):
        options.insert(0, (default, "Registro seleccionado · " + str(default)[:8]))
    return dict(
        name=name,
        label=label,
        type="select",
        options=options,
        default=default,
        required=required,
        lookup=url_for("selectors.options", source=source),
        has_more=data["has_more"],
    )


@bp.get("/opciones/<source>")
def options(source):
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        raise BusinessError("Página inválida.", 422) from None
    return jsonify(fetch(source, page, request.args.get("q", "").strip()))
