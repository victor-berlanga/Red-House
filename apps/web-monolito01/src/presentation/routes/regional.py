"""Interfaz del proceso regional; validación y autorización en servicios."""
import psycopg
from flask import Blueprint,g,render_template,request,redirect,url_for,flash
from ..workflow import progress

from ..views import regional_value
from ...business import validators as v
from ...business.access import require,BusinessError
from ...business.services import regional as svc,matching,logistics
from ...data_access.connection import transaction
from ...data_access.repositories import network,inventory
from ...data_access.repositories.common import scope

bp=Blueprint('regional',__name__,url_prefix='/sangre')


@bp.get('/panel-regional')
def dashboard():
    from ...business.services.regional_reporting import dashboard as report
    from ..timezones import selected_zone
    links={
        'Unidades disponibles':url_for('inventory.index',effective_status='AVAILABLE'),
        'Próximas a caducar':url_for('inventory.index',expiry='soon'),
        'Solicitudes activas':url_for('regional.requests',status='ACTIVE'),
        'Solicitudes urgentes':url_for('regional.requests',status='ACTIVE',urgency='URGENT'),
    }
    if g.principal.can('logistics') or g.principal.can('trace.read'):
        links['Recursos reservados']=url_for('regional.allocations',status='ACTIVE',direction='destination')
        links['Traslados activos']=url_for('regional.allocations',shipment_status='ACTIVE',direction='destination')
    return render_template('regional/dashboard.html',title='Panel regional',active='regional',stat_links=links,**report(g.principal,selected_zone()))


def field(name,label,options=None,kind='text',required=True,value='',limit=1000):
    from ..timezones import selected_zone
    label=label.replace('UTC',selected_zone())
    if name in ('restrictions','background','requirement','studies','reason','observation','justification','release_reference','source_reference'):
        kind='textarea'
    group = 'Datos y referencias' if name in ('institution_id','record_code','display_name','blood_group','donor_id','recipient_id','donation_code','request_code') else 'Información del proceso'
    if name.startswith('consent_') or name=='human_confirmation': group='Consentimiento y autorización'
    return dict(name=name,label=label,options=options,kind=kind,required=required,value=value,limit=limit,group=group)


def form(title,action,fields,button=None,version=None):
    error = getattr(g,'form_error',None) if action == request.path else None
    if error:
        for f in fields:
            f['value']=request.form.get(f['name'],'')
        # No sustituir una versión obsoleta por la nueva sin revisión del usuario.
        if version is not None: version=request.form.get('version_no','')
    return dict(title=title,action=action,fields=fields,button=button or title,version=version,error=error)


def display_path():
    return getattr(g,'display_path',request.path)


def fragment():
    return request.method=='GET' and request.headers.get('X-Filter-Fragment')=='1'



def page(title,*,active,rows=None,columns=None,forms=None,facts=None,total=None,number=1,note='',links=None,workflow=None):
    from ..timezones import selected_zone
    columns=[(key,label.replace('UTC',selected_zone())) for key,label in (columns or [])]
    facts=[(label.replace('UTC',selected_zone()),value) for label,value in (facts or [])]
    filters=[]
    if active=='solicitudes':
        filters=[('status','Estado',['ACTIVE','OPEN','IN_PROGRESS','CLOSED','CANCELLED']),('urgency','Urgencia',['URGENT','PRIORITY','ROUTINE'])]
    elif active=='donaciones': filters=[('status','Estado',['REGISTERED','COLLECTED','PROCESSED','CANCELLED'])]
    elif active in ('traslados','trazabilidad'):
        filters=[('direction','Dirección',['destination']),('status','Asignación',['ACTIVE','RESERVED','ASSIGNED','RECEIVED','CANCELLED']),('shipment_status','Traslado',['ACTIVE','SCHEDULED','PREPARED','COLLECTED','IN_TRANSIT','DELIVERED','ACCEPTED','CANCELLED'])]
    return render_template('regional/page.html',title=title,active=active,rows=rows,columns=columns or [],
        forms=forms or [],facts=facts or [],total=total,page=number,note=note,links=links or [],
        filter_fields=filters,listing_url=display_path(),workflow=workflow,form_error=getattr(g,'form_error',None))



def options(entity):
    with transaction() as conn:
        query,params=network.query_for(entity,g.principal)
        rows=conn.execute(query,params).fetchall()
        key=network.ENTITIES[entity][1];label=network.ENTITIES[entity][2]
        return [(str(r[key]),r[label]) for r in rows]


def person_options(kind):
    require(g.principal,'donor.write' if kind=='donor' else 'recipient.write')
    with transaction() as conn:
        clause,params=scope(g.principal,'i')
        # Constante de ruta, no nombre suministrado por el formulario.
        if kind=='donor':
            clause+=" AND p.current_status='ELIGIBLE' AND (SELECT decision FROM donor_review WHERE donor_id=p.donor_id ORDER BY occurred_at DESC,review_id DESC LIMIT 1)='ELIGIBLE'"
        else: clause+=" AND p.current_status='ACTIVE'"
        rows=conn.execute(f'SELECT p.{kind}_id,p.record_code,p.display_name FROM {kind} p JOIN institution i USING(institution_id) WHERE '+clause+' ORDER BY p.record_code',params).fetchall()
        return [(str(r[kind+'_id']),r['record_code']+' · '+r['display_name']) for r in rows]


@bp.route('/personas/<kind>',methods=['GET','POST'])
def people(kind):
    if kind not in ('donor','recipient'):
        raise BusinessError('La sección no existe.',404)
    if request.method=='POST' and not getattr(g,'form_error',None):
        identifier=svc.save_person(g.principal,kind,request.form)
        return redirect(url_for('regional.person_detail',kind=kind,identifier=identifier))
    n=v.integer({'page':request.args.get('page',1)},'page',1,100000)
    rows,total=svc.people(g.principal,kind,request.args.get('q','')[:100],n)
    for row in rows:
        row['detail_url']=url_for('regional.person_detail',kind=kind,identifier=row[kind+'_id'])
    return page('Donantes' if kind=='donor' else 'Receptores',active='donantes' if kind=='donor' else 'receptores',rows=rows,total=total,number=n,
        columns=[('record_code','Expediente'),('display_name','Nombre'),('blood_group','ABO/Rh'),('institution_name','Institución'),('current_status','Estado')],
        forms=[] if fragment() else [form('Registrar expediente',url_for('regional.people',kind=kind),person_fields(kind))],
        note='')


def person_fields(kind,data=None):
    fields=[field('institution_id','Institución',options('institutions')),field('record_code','Folio del expediente',limit=30),
            field('display_name','Nombre',limit=120),field('blood_group','ABO/Rh registrado',[(k,k) for k in inventory.GROUPS]),
            field('restrictions','Restricciones documentadas o “ninguna registrada”')]
    if kind=='donor':
        fields += [field('donation_kind','Tipo de donación',[('VOLUNTARY','Voluntaria'),('REPLACEMENT','Reposición')]),
            field('background','Antecedentes'),field('consent_reference','Referencia del consentimiento',limit=240),
            field('consent_at','Fecha del consentimiento (UTC)',kind='datetime-local')]
    else:
        fields += [field('requirement','Requerimiento registrado'),field('urgency','Urgencia registrada',[('URGENT','Urgente'),('PRIORITY','Prioritaria'),('ROUTINE','Ordinaria')]),field('studies','Estudios y referencias'),
                   field('current_status','Estado',[('ACTIVE','Activo'),('INACTIVE','Inactivo')])]
    for f in fields:
        if data and f['name'] in data:
            val=data[f['name']]
            from ..timezones import inputfmt
            f['value']=inputfmt(val) if f['kind']=='datetime-local' else str(val)
    return fields


@bp.route('/personas/<kind>/<uuid:identifier>',methods=['GET','POST'])
def person_detail(kind,identifier):
    if kind not in ('donor','recipient'):
        raise BusinessError('La sección no existe.',404)
    if request.method=='POST' and not getattr(g,'form_error',None):
        svc.save_person(g.principal,kind,request.form,identifier)
        return redirect(display_path())
    row,reviews=svc.person_detail(g.principal,kind,identifier)
    with transaction() as conn:
        locked=bool(conn.execute('SELECT 1 FROM donation WHERE donor_id=%s LIMIT 1' if kind=='donor' else 'SELECT 1 FROM blood_request WHERE recipient_id=%s LIMIT 1',(identifier,)).fetchone())
    fields=person_fields(kind,row)
    forms=[] if locked else [form('Actualizar expediente',display_path(),fields,version=row['version_no'])]
    facts=[('Institución',row['institution_name']),('Estado',row['current_status'])]
    if locked:
        facts += [(f['label'],dict(f['options']).get(str(row.get(f['name'])),row.get(f['name'])) if f['options'] is not None else row.get(f['name'])) for f in fields if f['name']!='institution_id']

    if kind=='donor' and g.principal.can('donor.review'):
        forms.append(form('Registrar evaluación del donante',url_for('regional.review',identifier=identifier),[
            field('decision','Decisión registrada',[('ELIGIBLE','Elegible'),('DEFERRED','Diferido')]),
            field('reason','Fundamento de la decisión'),field('human_confirmation','Confirmo que realicé la evaluación y autorizo la decisión registrada',kind='checkbox')],version=row['version_no']))
    return page('Expediente '+row['record_code'],active='donantes' if kind=='donor' else 'receptores',facts=facts,workflow=progress('donor' if kind=='donor' else 'recipient',row['current_status']),
        rows=reviews,columns=[('occurred_at','Fecha UTC'),('decision','Decisión humana'),('party_name','Responsable'),('reason','Fundamento restringido')],forms=forms,
        note=('Expediente de consulta: sus datos respaldan donaciones o solicitudes y se conserva su historia.' if locked else 'Al actualizar los datos del donante se requiere una nueva evaluación.' if kind=='donor' else ''))


@bp.post('/donantes/<uuid:identifier>/revision')
def review(identifier):
    svc.review_donor(g.principal,identifier,request.form)
    return redirect(url_for('regional.person_detail',kind='donor',identifier=identifier))


@bp.route('/donaciones',methods=['GET','POST'])
def donations():
    if request.method=='POST' and not getattr(g,'form_error',None):
        identifier=svc.create_donation(g.principal,request.form)
        return redirect(url_for('regional.donation_detail',identifier=identifier))
    n=v.integer({'page':request.args.get('page',1)},'page',1,100000)
    rows,total=svc.donations(g.principal,n,request.args.get('q','')[:100],request.args.get('status',''))
    for row in rows:
        row['detail_url']=url_for('regional.donation_detail',identifier=row['donation_id'])
    forms=[]
    if g.principal.can('donation.write') and not fragment():
        forms=[form('Registrar donación',display_path(),[field('donation_code','Folio de donación',limit=30),field('donor_id','Donante con revisión favorable',person_options('donor'))])]
    return page('Donación, recolección y procesamiento',active='donaciones',rows=rows,total=total,number=n,
        columns=[('donation_code','Donación'),('donor_code','Expediente'),('institution_name','Institución'),('current_status','Estado')],forms=forms)


@bp.route('/donaciones/<uuid:identifier>',methods=['GET','POST'])
def donation_detail(identifier):
    if request.method=='POST' and not getattr(g,'form_error',None):
        svc.progress_donation(g.principal,identifier,request.form)
        return redirect(display_path())
    with transaction() as conn:
        row=svc.donation_row(conn,g.principal,identifier)
        history=conn.execute('SELECT e.*,p.party_name FROM donation_event e JOIN user_account u ON u.account_id=e.actor_id JOIN party p USING(party_id) WHERE donation_id=%s ORDER BY occurred_at,event_id',(identifier,)).fetchall()
        units=conn.execute('SELECT b.resource_id,b.traceability_code FROM donation_unit d JOIN resource b USING(resource_id) WHERE donation_id=%s',(identifier,)).fetchall()
        svc.event(conn,g.principal,'SENSITIVE_READ','DONATION',identifier,row['institution_id'])
    forms=[]
    allowed={'REGISTERED':[('COLLECTED','Registrar recolección'),('CANCELLED','Cancelar')],'COLLECTED':[('PROCESSED','Registrar procesamiento'),('CANCELLED','Cancelar')]}
    if row['current_status'] in allowed and g.principal.can('donation.write'):
        forms.append(form('Registrar etapa',display_path(),[field('status','Evento',allowed[row['current_status']]),field('observation','Observación / referencia del procedimiento')],version=row['version_no']))
    if row['current_status']=='PROCESSED' and g.principal.can('unit.release'):
        forms.append(form('Liberar unidad / componente',url_for('regional.produce',identifier=identifier),[
            field('traceability_code','Folio de unidad',limit=30),field('component_id','Componente',options('components')),
            field('location_id','Ubicación',options('locations')),field('expires_at','Caducidad (UTC)',kind='datetime-local'),
            field('release_reference','Referencia de pruebas y liberación autorizada',limit=240),
            field('human_confirmation','Confirmo la revisión de pruebas y autorizo la liberación de la unidad',kind='checkbox')]))
    return page(row['donation_code'],active='donaciones',facts=[('Expediente',row['donor_code']),('Estado',row['current_status']),('ABO/Rh',row['blood_group'])],
        rows=history,columns=[('occurred_at','Fecha UTC'),('status','Etapa'),('party_name','Responsable'),('observation','Evidencia registrada')],forms=forms,
        links=[(u['traceability_code'],url_for('inventory.detail',identifier=u['resource_id'])) for u in units],
        workflow=progress('donation', 'RELEASED' if units else row['current_status']),note='Cada etapa conserva su fecha, responsable y referencia del procedimiento.')


@bp.post('/donaciones/<uuid:identifier>/unidades')
def produce(identifier):
    rid=svc.produce_unit(g.principal,identifier,request.form)
    return redirect(url_for('inventory.detail',identifier=rid))


@bp.route('/solicitudes',methods=['GET','POST'])
def requests():
    if request.method=='POST' and not getattr(g,'form_error',None):
        identifier=svc.create_request(g.principal,request.form)
        return redirect(url_for('regional.request_detail',identifier=identifier))
    n=v.integer({'page':request.args.get('page',1)},'page',1,100000)
    rows,total=svc.requests_list(g.principal,n,request.args.get('q','')[:100],request.args.get('status',''),request.args.get('urgency',''))
    for row in rows:
        row['detail_url']=url_for('regional.request_detail',identifier=row['request_id'])
    forms=[]
    if g.principal.can('request.write') and not fragment():
        forms=[form('Crear solicitud de receptor',display_path(),[field('request_code','Folio de solicitud',limit=30),
            field('recipient_id','Receptor',person_options('recipient')),field('component_id','Componente',options('components')),
            field('quantity','Cantidad de unidades',kind='number'),field('urgency','Urgencia registrada',[('URGENT','Urgente'),('PRIORITY','Prioritaria'),('ROUTINE','Ordinaria')]),
            field('justification','Justificación clínica (acceso médico)')])]
    return page('Solicitudes regionales',active='solicitudes',rows=rows,total=total,number=n,forms=forms,
        columns=[('request_code','Solicitud'),('institution_name','Institución'),('component_name','Componente'),('blood_group','ABO/Rh'),('quantity','Cantidad'),('urgency','Urgencia'),('current_status','Estado')],
        note='Solicitudes ordenadas por urgencia y antigüedad.')


@bp.get('/solicitudes/<uuid:identifier>')
def request_detail(identifier):
    with transaction() as conn:
        row=svc.request_row(conn,g.principal,identifier)
        evaluation=conn.execute('SELECT * FROM candidate_evaluation WHERE request_id=%s ORDER BY occurred_at DESC,evaluation_id DESC LIMIT 1',(identifier,)).fetchone()
        candidates=conn.execute('''SELECT c.*,b.traceability_code,i.institution_name FROM blood_candidate c JOIN resource b USING(resource_id)
            JOIN blood_inventory i USING(resource_id) WHERE evaluation_id=%s ORDER BY rank_no''',(evaluation['evaluation_id'],)).fetchall() if evaluation else []
        allocations=conn.execute('SELECT a.allocation_id,b.traceability_code,a.current_status FROM blood_allocation a JOIN resource b USING(resource_id) WHERE request_id=%s ORDER BY reserved_at',(identifier,)).fetchall()
        svc.event(conn,g.principal,'SENSITIVE_READ' if g.principal.can('request.write') else 'READ','BLOOD_REQUEST',identifier,row['institution_id'])
    forms=[]
    live_allocations=[a for a in allocations if a['current_status']!='CANCELLED']
    active=row['current_status'] in ('OPEN','IN_PROGRESS')
    if active and g.principal.can('candidate.evaluate'):
        forms.append(form('Buscar candidatos regionales',url_for('regional.evaluate',identifier=identifier),[],button='Evaluar ABO/Rh y ordenar alternativas'))
    if active and g.principal.can('allocation.authorize') and candidates:
        forms.append(form('Autorización médica y reserva',url_for('regional.reserve',identifier=identifier),[
            field('candidate_id','Unidad potencialmente compatible',[(str(c['candidate_id']),f"{c['rank_no']}. {c['traceability_code']} · {c['institution_name']}") for c in candidates]),
            field('reason','Referencia / motivo de autorización, sin datos personales',limit=240),
            field('human_confirmation','He revisado estudios, restricciones y resultado; autorizo esta reserva',kind='checkbox')],button='Autorizar y reservar una unidad',version=row['version_no']))
    if active and g.principal.can('request.write'):
        forms.append(form('Cerrar o cancelar solicitud',url_for('regional.close_request',identifier=identifier),[
            field('status','Acción',[('CLOSED','Cerrar tras recibir la cantidad completa'),('CANCELLED','Cancelar sin reservas activas ni entregas')]),field('observation','Motivo sin datos clínicos',limit=240)],version=row['version_no']))
    facts=[('Institución solicitante',row['institution_name']),('Componente',row['component_name']),('ABO/Rh',row['blood_group']),('Cantidad',row['quantity']),('Urgencia',row['urgency']),('Estado',row['current_status']),('Fecha UTC',row['requested_at'])]
    if g.principal.can('request.write'):
        facts += [('Justificación restringida',row['justification'])]
    if evaluation:
        facts += [('Versión del algoritmo',evaluation['algorithm_version']),('Evaluación UTC',evaluation['occurred_at']),('Tiempo de cálculo (ms)',evaluation['elapsed_ms'])]
    return page(row['request_code'],active='solicitudes',facts=facts,rows=candidates,forms=forms,
        columns=[('rank_no','Orden'),('traceability_code','Unidad'),('institution_name','Origen'),('donor_group','ABO/Rh unidad'),('distance_km','Distancia (km)'),('travel_minutes','Minutos estimados'),('expires_at','Caducidad UTC'),('explanation','Factores y límites')],
        links=[(a['traceability_code']+' · '+regional_value(a['current_status'],'current_status'),url_for('regional.allocation_detail',identifier=a['allocation_id'])) for a in allocations],
        workflow=progress('request', 'CLOSED' if row['current_status']=='CLOSED' else 'CANCELLED' if row['current_status']=='CANCELLED' else 'RECEIVED' if live_allocations and len(live_allocations)==row['quantity'] and all(a['current_status']=='RECEIVED' for a in live_allocations) else 'RESERVED' if live_allocations else 'EVALUATED' if evaluation else 'OPEN'),note=matching.NOTICE+' Evaluación disponible para concentrados eritrocitarios.')


@bp.post('/solicitudes/<uuid:identifier>/evaluar')
def evaluate(identifier):
    matching.evaluate(g.principal,identifier)
    return redirect(url_for('regional.request_detail',identifier=identifier))


@bp.post('/solicitudes/<uuid:identifier>/reservar')
def reserve(identifier):
    aid=matching.reserve(g.principal,identifier,request.form)
    return redirect(url_for('regional.allocation_detail',identifier=aid))


@bp.post('/solicitudes/<uuid:identifier>/cerrar')
def close_request(identifier):
    svc.close_request(g.principal,identifier,request.form)
    return redirect(url_for('regional.request_detail',identifier=identifier))


@bp.route('/rutas',methods=['GET','POST'])
def routes():
    require(g.principal,'route.write')
    if request.method=='POST' and not getattr(g,'form_error',None):
        svc.save_route(g.principal,request.form)
        return redirect(display_path())
    with transaction() as conn:
        clause,params=scope(g.principal,'i')
        rows=conn.execute('''SELECT t.*,i.institution_name AS origin_name,d.institution_name AS destination_name FROM regional_route t
            JOIN institution i ON i.institution_id=t.origin_id JOIN institution d ON d.institution_id=t.destination_id WHERE '''+clause,params).fetchall()
        svc.event(conn,g.principal,'READ','REGIONAL_ROUTE','LIST',g.principal.institution_id)
    institutions=options('institutions')
    return page('Rutas y estimaciones regionales',active='rutas',rows=rows,columns=[('origin_name','Origen'),('destination_name','Destino'),('distance_km','Km'),('travel_minutes','Minutos'),('source_reference','Fuente / supuesto'),('version_no','Versión')],
        forms=[form('Registrar o actualizar ruta',display_path(),[field('origin_id','Origen',institutions),field('destination_id','Destino',institutions),
            field('distance_km','Distancia (km)',kind='number'),field('travel_minutes','Tiempo estimado (minutos)',kind='number'),
            field('source_reference','Fuente de la estimación',limit=240)])],note='Registra la distancia y el tiempo estimado del origen al destino. Incluye rutas internas para traslados dentro de una institución.')


@bp.get('/traslados')
def allocations():
    n=v.integer({'page':request.args.get('page',1)},'page',1,100000)
    rows,total=logistics.list_allocations(g.principal,n,request.args.get('q','')[:100],request.args.get('status',''),request.args.get('shipment_status',''),request.args.get('direction',''))
    for row in rows:
        row['detail_url']=url_for('regional.allocation_detail',identifier=row['allocation_id'])
    return page('Asignación, traslados y custodia',active='traslados' if g.principal.can('logistics') else 'trazabilidad',rows=rows,total=total,number=n,
        columns=[('traceability_code','Recurso'),('request_code','Solicitud'),('origin_name','Origen'),('destination_name','Destino'),('current_status','Asignación'),('shipment_status','Traslado')])


@bp.get('/traslados/<uuid:identifier>')
def allocation_detail(identifier):
    with transaction() as conn:
        row=logistics.allocation_row(conn,g.principal,identifier)
        shipment=conn.execute('SELECT * FROM shipment WHERE allocation_id=%s',(identifier,)).fetchone()
        history=conn.execute('''SELECT e.*,p.party_name FROM custody_event e JOIN user_account u ON u.account_id=e.actor_id
            JOIN party p USING(party_id) WHERE shipment_id=%s ORDER BY sequence''',(shipment['shipment_id'],)).fetchall() if shipment else []
        transports=conn.execute('''SELECT u.account_id,p.party_name FROM user_account u JOIN party p USING(party_id)
            JOIN account_role a USING(account_id) WHERE a.role_code='TRANSPORT' AND a.institution_id=%s AND u.account_status='ACTIVE' ''',(row['origin_id'],)).fetchall() if g.principal.can('shipment.plan') else []
        svc.event(conn,g.principal,'READ','BLOOD_ALLOCATION',identifier,g.principal.institution_id or row['origin_id'])
    forms=[]
    if row['current_status']=='RESERVED' and g.principal.can('shipment.plan'):
        forms.append(form('Asignar y programar traslado',url_for('regional.plan',identifier=identifier),[
            field('transport_id','Personal de traslado del origen',[(str(t['account_id']),t['party_name']) for t in transports]),
            field('vehicle','Vehículo',limit=120),field('departure_at','Salida prevista (UTC)',kind='datetime-local'),field('eta','ETA (UTC)',kind='datetime-local')],version=row['version_no']))
    if row['current_status'] in ('RESERVED','ASSIGNED') and g.principal.can('shipment.plan'):
        forms.append(form('Cancelar antes de recolección',url_for('regional.cancel',identifier=identifier),[field('observation','Motivo de cancelación',limit=240)],version=row['version_no']))
    if shipment and shipment['current_status'] not in ('ACCEPTED','CANCELLED') and g.principal.can('logistics'):
        next_status={'SCHEDULED':'PREPARED','PREPARED':'COLLECTED','COLLECTED':'IN_TRANSIT','IN_TRANSIT':'DELIVERED','DELIVERED':'ACCEPTED'}[shipment['current_status']]
        permitted=(next_status=='PREPARED' and g.principal.role_code=='OPERATOR' and g.principal.institution_id==row['origin_id']) or (next_status=='ACCEPTED' and g.principal.role_code in ('OPERATOR','MEDICAL') and g.principal.institution_id==row['destination_id']) or (next_status in ('COLLECTED','IN_TRANSIT','DELIVERED') and g.principal.role_code=='TRANSPORT' and shipment['transport_id']==g.principal.account_id)
        choices=[('INCIDENT','Registrar incidencia sin avanzar estado')]
        if permitted:
            choices.insert(0,(next_status,{'PREPARED':'Preparado / entregado para recolección','COLLECTED':'Recolectado / recibido por transportista','IN_TRANSIT':'En tránsito','DELIVERED':'Entregado en destino','ACCEPTED':'Recibido y aceptado por institución'}[next_status]))
        fields=[field('status','Evento',choices),field('location_description','Ubicación del evento',limit=240),field('observation','Observación sin datos clínicos'),field('evidence_reference','Referencia de evidencia / acta',limit=240)]
        if next_status=='ACCEPTED' and permitted:
            fields.append(field('location_id','Ubicación receptora (para aceptación)',options('locations'),required=False))
        forms.append(form('Registrar evento de custodia',url_for('regional.step',identifier=identifier),fields,version=shipment['version_no']))
    facts=[('Recurso',row['traceability_code']),('Solicitud',row['request_code']),('Origen',row['origin_name']),('Destino',row['destination_name']),('Asignación',row['current_status']),('Autorizado por (cuenta)',row['authorized_by'])]
    if shipment:
        facts += [('Traslado',shipment['current_status']),('Vehículo',shipment['vehicle']),('Salida prevista UTC',shipment['departure_at']),('ETA UTC',shipment['eta'])]
    return page('Trazabilidad de '+row['traceability_code'],active='traslados' if g.principal.can('logistics') else 'trazabilidad',facts=facts,rows=history,forms=forms,
        columns=[('sequence','Secuencia'),('occurred_at','Fecha UTC'),('status','Evento'),('party_name','Responsable'),('location_description','Ubicación'),('observation','Observación'),('evidence_reference','Referencia de evidencia')],
        workflow=progress('shipment',shipment['current_status'] if shipment else row['current_status']),note='Historial de custodia: cada evento conserva responsable, fecha, ubicación y referencia de evidencia.')


@bp.post('/traslados/<uuid:identifier>/programar')
def plan(identifier):
    logistics.plan(g.principal,identifier,request.form)
    return redirect(url_for('regional.allocation_detail',identifier=identifier))


@bp.post('/traslados/<uuid:identifier>/cancelar')
def cancel(identifier):
    logistics.cancel(g.principal,identifier,request.form)
    return redirect(url_for('regional.allocation_detail',identifier=identifier))


@bp.post('/traslados/<uuid:identifier>/evento')
def step(identifier):
    logistics.step(g.principal,identifier,request.form)
    return redirect(url_for('regional.allocation_detail',identifier=identifier))


def redisplay(error):
    if request.method != 'POST' or error.status not in (400,409) or getattr(g,'form_error',None):
        from ..errors import business_error
        return business_error(error)
    parents={'review':'person_detail','produce':'donation_detail','evaluate':'request_detail',
             'reserve':'request_detail','close_request':'request_detail','plan':'allocation_detail',
             'cancel':'allocation_detail','step':'allocation_detail'}
    name=request.endpoint.split('.')[-1]
    parent=parents.get(name,name)
    args=dict(request.view_args)
    if name=='review': args['kind']='donor'
    g.form_error=error
    g.display_path=url_for('regional.'+parent,**args)
    response=globals()[parent](**args)
    return response,error.status


@bp.errorhandler(BusinessError)
def recover_business_error(error):
    return redisplay(error)


@bp.errorhandler(psycopg.IntegrityError)
def recover_integrity_error(error):
    return redisplay(BusinessError('El folio ya existe o una referencia impide guardar. Revisa los datos; no se aplicó el cambio.',409))
