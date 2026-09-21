from datetime import date

from flask import Blueprint, g, render_template, request, redirect, url_for

from ...business import validators as v
from ...business.access import BusinessError, require
from ...business.services import reporting
from ..views import FUTURE

bp = Blueprint("portal", __name__)


@bp.get("/panel")
def dashboard():
    if g.principal.role_code == 'TRANSPORT':
        return redirect(url_for('regional.allocations'))
    if g.principal.role_code in ('COORDINATOR','MEDICAL'):
        return redirect(url_for('regional.dashboard'))
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
    from ..timezones import selected_zone
    filters['timezone']=selected_zone()
    rows, total = reporting.audit_list(g.principal, filters, page)
    return render_template("audit.html", title="Bitácora de auditoría", active="audit", rows=rows, total=total, page=page)


@bp.get("/proximamente/<slug>")
def future(slug):
    require(g.principal, "preview")
    destinations = {
        'donantes': ('regional.people', {'kind':'donor'}),
        'receptores': ('regional.people', {'kind':'recipient'}),
        'solicitudes': ('regional.requests', {}), 'compatibilidad': ('regional.requests', {}),
        'traslados': ('regional.allocations', {}), 'custodia': ('regional.allocations', {})}
    if slug in destinations:
        endpoint, args = destinations[slug]
        return redirect(url_for(endpoint, **args))
    if slug not in FUTURE:
        raise BusinessError("La vista no existe.", 404)
    return render_template("future.html", title=FUTURE[slug]["title"], active=slug, view=FUTURE[slug], slug=slug)


@bp.get('/auditoria/<uuid:identifier>')
def audit_detail(identifier):
    require(g.principal,'audit.read')
    from ...data_access.connection import transaction
    from ...data_access.repositories import audit as audit_repo
    from ..timezones import datefmt
    with transaction() as conn:
        column='a.institution_id' if g.principal.institution_id else 'a.region_name'
        value=g.principal.institution_id or g.principal.region_name
        row=conn.execute("SELECT a.*,coalesce(p.party_name,'No identificado') AS actor_name FROM audit_event a LEFT JOIN user_account u ON u.account_id=a.actor_id LEFT JOIN party p USING(party_id) WHERE "+column+'=%s AND a.event_id=%s',(value,identifier)).fetchone()
        if not row:
            raise BusinessError('El evento no está disponible en tu ámbito.',404)
        changes=conn.execute('SELECT * FROM audit_change WHERE event_id=%s ORDER BY field_name',(identifier,)).fetchall()
        audit_repo.record(conn,g.principal,'READ','AUDIT_EVENT',identifier,'Consulta de evidencia de auditoría')
    facts=[('Fecha',datefmt(row['occurred_at'])),('Actor',row['actor_name']),('Acción',row['action']),('Entidad',row['entity_type']),('Referencia',row['entity_reference']),('Resultado',{'SUCCESS':'Correcto','DENIED':'Denegado','FAILED':'Fallido'}.get(row['outcome'],row['outcome'])),('Motivo',row['reason']),('Correlación',row['correlation_id'])]
    facts += [(c['field_name'],f"{c['previous_value'] if c['previous_value'] is not None else '—'} → {c['new_value'] if c['new_value'] is not None else '—'}") for c in changes]
    return render_template('record_detail.html',title='Detalle del evento',active='audit',facts=facts)


@bp.post('/preferencias/horario')
def timezone_preference():
    from urllib.parse import urlsplit
    from ..timezones import ZONES
    zone=v.choice(request.form,'timezone',ZONES,'zona horaria')
    target=request.form.get('next','/panel')
    parsed=urlsplit(target)
    if parsed.scheme or parsed.netloc or not target.startswith('/') or target.startswith('//') or '\\' in target or any(ord(c)<32 for c in target):
        target='/panel'
    response=redirect(target)
    response.set_cookie('display_timezone',zone,max_age=31536000,httponly=True,samesite='Lax',secure=request.is_secure)
    return response
