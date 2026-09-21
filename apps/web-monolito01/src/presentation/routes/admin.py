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
    return render_template("admin/list.html", title=TITLES[entity], active="institutions" if entity in ("sites", "locations") else entity, entity=entity,
                           rows=rows, total=total, page=page, metadata=network.ENTITIES[entity])


@bp.route("/<entity>/nuevo", methods=["GET", "POST"])
@bp.route("/<entity>/<uuid:identifier>/editar", methods=["GET", "POST"])
def form(entity, identifier=None):
    check_entity(entity)
    if entity == 'components' and g.principal.institution_id:
        raise BusinessError('El catálogo regional requiere un administrador regional.', 403)
    if entity == 'institutions' and not identifier and g.principal.institution_id:
        raise BusinessError('Solo la administración regional puede incorporar instituciones.', 403)
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
    original = {key: value for key, value in data.items() if key not in ('password', 'password_hash')}
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
                           active="institutions" if entity in ("sites", "locations") else entity, entity=entity, data=data, choices=choices,
                           identifier=identifier, error=error, original=original), status


@bp.get('/<entity>/<uuid:identifier>')
def detail(entity, identifier):
    check_entity(entity)
    fields = {
        'institutions': [('institution_code','Código'),('institution_name','Institución'),('institution_type','Tipo'),('participation_status','Participación'),('region_name','Región'),('city','Ciudad'),('street','Dirección'),('operating_hours','Horarios'),('contact_name','Contacto'),('contact_email','Correo del contacto'),('contact_phone','Teléfono del contacto'),('capability_names','Capacidades')],
        'sites': [('site_code','Código'),('site_name','Sede'),('institution_name','Institución'),('region_name','Región'),('city','Ciudad'),('street','Dirección'),('site_status','Estado')],
        'locations': [('location_code','Código'),('location_description','Descripción'),('institution_name','Institución'),('site_name','Sede'),('region_name','Región'),('is_active','Activo')],
        'components': [('component_code','Código'),('component_name','Componente'),('region_name','Región'),('is_active','Activo')],
        'users': [('party_name','Nombre'),('login_email','Correo'),('role_name','Perfil'),('institution_name','Institución'),('region_name','Región'),('account_status','Estado')],
    }
    with transaction() as conn:
        row = network.one(conn, entity, g.principal, identifier)
        if not row:
            raise BusinessError('El registro no está disponible en tu ámbito.',404)
        if entity == 'institutions':
            row.update(network.institution_details(conn, identifier))
            row['capability_names'] = ', '.join(r['capability_name'] for r in conn.execute('SELECT c.capability_name FROM institution_capability ic JOIN capability c USING(capability_code) WHERE institution_id=%s ORDER BY c.capability_name',(identifier,)))
        audit.record(conn,g.principal,'READ',network.ENTITIES[entity][0].upper(),identifier,'Consulta de detalle administrativo',institution_id=row.get('institution_id'))
    from ..views import regional_value
    facts = [(label, ('Sí' if row.get(key) else 'No') if key=='is_active' else regional_value(row.get(key),'current_status' if key in ('site_status','account_status') else key)) for key,label in fields[entity]]
    facts.append(('Versión', row.get('version_no')))
    return render_template('record_detail.html',title=row[network.ENTITIES[entity][2]],facts=facts,active='institutions' if entity in ('sites','locations') else entity)


@bp.route("/configuracion/parametros", methods=["GET", "POST"])
def settings():
    require(g.principal, "administration")
    error, status = None, 200
    if request.method == "POST":
        try:
            administration.save_parameter(g.principal, request.form)
            flash("Aviso de caducidad actualizado.", "success")
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
