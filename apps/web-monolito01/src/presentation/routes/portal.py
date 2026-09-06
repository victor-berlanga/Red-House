from datetime import date

from flask import Blueprint, g, render_template, request

from ...business import validators as v
from ...business.access import BusinessError, require
from ...business.services import reporting
from ..views import FUTURE

bp = Blueprint("portal", __name__)


@bp.get("/panel")
def dashboard():
    return render_template("dashboard.html", title="Panel principal", active="dashboard", **reporting.dashboard(g.principal))


@bp.get("/auditoria")
def audit():
    filters = {"q": v.text(request.args, "q", "la búsqueda", 100, False), "outcome": request.args.get("outcome", "")}
    if filters["outcome"] not in ("", "SUCCESS", "FAILED", "DENIED"):
        raise BusinessError("Selecciona un resultado válido.")
    if request.args.get("date"):
        try:
            filters["date"] = date.fromisoformat(request.args["date"])
        except ValueError:
            raise BusinessError("Selecciona una fecha válida.") from None
    page = v.integer({"page": request.args.get("page", 1)}, "page", 1, 100000)
    rows, total = reporting.audit_list(g.principal, filters, page)
    return render_template("audit.html", title="Bitácora de auditoría", active="audit", rows=rows, total=total, page=page)


@bp.get("/proximamente/<slug>")
def future(slug):
    require(g.principal, "preview")
    if slug not in FUTURE:
        raise BusinessError("La vista no existe.", 404)
    return render_template("future.html", title=FUTURE[slug]["title"], active=slug, view=FUTURE[slug], slug=slug)
