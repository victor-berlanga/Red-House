import psycopg
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ...business import validators as v
from ...business.access import BusinessError, require
from ...business.services import administration
from ...data_access.connection import transaction
from ...data_access.repositories import audit, network
from ..views import TITLES

bp = Blueprint("admin", __name__, url_prefix="/administracion")


def check_entity(entity):
    require(g.principal, "administration")
    if entity not in network.ENTITIES:
        raise BusinessError("La sección no existe.", 404)


@bp.get("/<entity>")
def index(entity):
    check_entity(entity)
    page = v.integer({"page": request.args.get("page", 1)}, "page", 1, 100000)
    query = v.text(request.args, "q", "la búsqueda", 100, False)
    state = request.args.get("state", "")
    if state not in ("", "ACTIVE", "INACTIVE"):
        raise BusinessError("Selecciona un estado válido.")
    with transaction() as conn:
        rows, total = network.listing(conn, entity, g.principal, query, state, page)
        audit.record(conn, g.principal, "READ", network.ENTITIES[entity][0].upper(), "LIST", "Consulta administrativa autorizada")
    return render_template("admin/list.html", title=TITLES[entity], active=entity, entity=entity,
                           rows=rows, total=total, page=page, metadata=network.ENTITIES[entity])


@bp.route("/<entity>/nuevo", methods=["GET", "POST"])
@bp.route("/<entity>/<uuid:identifier>/editar", methods=["GET", "POST"])
def form(entity, identifier=None):
    check_entity(entity)
    data, error, status = {}, None, 200
    with transaction() as conn:
        if identifier:
            data = network.one(conn, entity, g.principal, identifier)
            if not data:
                raise BusinessError("El registro no está disponible en tu ámbito.", 404)
            data.pop("password_hash", None)
            if entity == "institutions":
                data.update(network.institution_details(conn, identifier))
            if entity == "users":
                data["scope"] = str(data["institution_id"]) if data["institution_id"] else "REGIONAL"
            if request.method == "GET":
                audit.record(conn, g.principal, "READ", network.ENTITIES[entity][0].upper(), identifier,
                             "Consulta de detalle administrativo", institution_id=data.get("institution_id"))
        choices = network.options(conn, g.principal)
    if request.method == "POST":
        try:
            administration.save(entity, g.principal, request.form, identifier)
            flash("Cambios guardados en PostgreSQL y registrados en auditoría.", "success")
            return redirect(url_for("admin.index", entity=entity))
        except BusinessError as exc:
            if exc.status not in (400, 409):
                raise
            error, status = exc.message, exc.status
        except psycopg.IntegrityError:
            error, status = "El código o correo ya está registrado, o existe una referencia no válida. Revisa los datos.", 409
        data = request.form.to_dict()
        data.pop("password", None)
        data["capabilities"] = request.form.getlist("capabilities")
        data["is_active"] = request.form.get("is_active") == "on"
    return render_template("admin/form.html", title=("Editar " if identifier else "Registrar ") + TITLES[entity].lower(),
                           active=entity, entity=entity, data=data, choices=choices,
                           identifier=identifier, error=error), status


@bp.route("/configuracion/parametros", methods=["GET", "POST"])
def settings():
    require(g.principal, "administration")
    error, status = None, 200
    if request.method == "POST":
        try:
            administration.save_parameter(g.principal, request.form)
            flash("Nueva versión del umbral DEMO guardada.", "success")
            return redirect(url_for("admin.settings"))
        except BusinessError as exc:
            if exc.status not in (400, 409):
                raise
            error, status = exc.message, exc.status
    with transaction() as conn:
        roles = conn.execute("SELECT * FROM role ORDER BY is_enabled DESC, role_name").fetchall()
        parameter = network.parameter(conn, g.principal.region_name)
        transitions = conn.execute("SELECT * FROM blood_status_transition ORDER BY previous_status,new_status").fetchall()
    return render_template("admin/settings.html", title="Roles y parámetros", active="settings", roles=roles,
                           parameter=parameter, transitions=transitions, error=error), status
