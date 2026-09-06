import psycopg
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ...business import validators as v
from ...business.access import BusinessError, require
from ...business.services import inventory as service
from ...data_access.connection import transaction
from ...data_access.repositories import audit, inventory as repo, network

bp = Blueprint("inventory", __name__, url_prefix="/inventario")


@bp.get("")
def index():
    require(g.principal, "inventory.read")
    filters = {"q": v.text(request.args, "q", "la búsqueda", 100, False)}
    for key in ("institution_id", "component_id"):
        if request.args.get(key):
            filters[key] = v.identifier(request.args, key)
    for key, allowed in (("effective_status", repo.STATUSES), ("recorded_group_code", repo.GROUPS), ("expiry", ("soon", "expired"))):
        if request.args.get(key):
            filters[key] = v.choice(request.args, key, allowed, key)
    page = v.integer({"page": request.args.get("page", 1)}, "page", 1, 100000)
    with transaction() as conn:
        parameter = network.parameter(conn, g.principal.region_name)
        hours = parameter["scalar_value"] if parameter else 72
        rows, total = repo.listing(conn, g.principal, filters, hours, page)
        choices = network.options(conn, g.principal)
        stats, _, _ = repo.summary(conn, g.principal, hours)
        audit.record(conn, g.principal, "READ", "BLOOD_UNIT", "LIST", "Consulta paginada de inventario autorizado")
    return render_template("inventory/list.html", title="Inventario sanguíneo", active="inventory", rows=rows,
                           total=total, page=page, choices=choices, hours=hours, stats=stats, groups=repo.GROUPS)


@bp.route("/nueva", methods=["GET", "POST"])
def create():
    require(g.principal, "inventory.write")
    error, status = None, 200
    if request.method == "POST":
        try:
            identifier = service.create(g.principal, request.form)
            flash("Unidad DEMO registrada. Se guardó su primer movimiento y la auditoría.", "success")
            return redirect(url_for("inventory.detail", identifier=identifier))
        except BusinessError as exc:
            if exc.status != 400:
                raise
            error, status = exc.message, exc.status
        except psycopg.IntegrityError:
            error, status = "El folio ya está registrado o una referencia no es válida.", 409
    with transaction() as conn:
        choices = network.options(conn, g.principal)
    return render_template("inventory/form.html", title="Registrar unidad DEMO", active="inventory",
                           choices=choices, groups=repo.GROUPS, error=error, data=request.form), status


@bp.route("/<uuid:identifier>", methods=["GET", "POST"])
def detail(identifier):
    error, status = None, 200
    if request.method == "POST":
        try:
            service.change(g.principal, identifier, request.form)
            flash("Movimiento guardado con trazabilidad y auditoría.", "success")
            return redirect(url_for("inventory.detail", identifier=identifier))
        except BusinessError as exc:
            if exc.status not in (400, 409):
                raise
            error, status = exc.message, exc.status
    row, history = service.details(g.principal, identifier)
    with transaction() as conn:
        choices = network.options(conn, g.principal)
        permitted = conn.execute("SELECT new_status FROM blood_status_transition WHERE previous_status = %s",
                                 (row["current_status"],)).fetchall()
    return render_template("inventory/detail.html", title=row["traceability_code"], active="inventory", unit=row,
                           history=history, choices=choices, permitted=[r["new_status"] for r in permitted],
                           error=error), status
